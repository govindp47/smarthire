"""
Resume scoring routes: Calculate and update resume scores.
"""
import logging
from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status, BackgroundTasks
from sqlalchemy import select, update
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.database import get_db
from app.models import Resume, Job, User, ResumeData
from app.api.deps import get_current_user
from app.services.scoring import scoring_service

logger = logging.getLogger(__name__)
router = APIRouter()


async def score_resume_background(resume_id: UUID, job_id: UUID, db: AsyncSession):
    """
    Background task to score a resume.
    
    Args:
        resume_id: Resume ID to score
        job_id: Job ID for comparison
        db: Database session
    """
    try:
        # Get resume with parsed data
        result = await db.execute(
            select(Resume)
            .options(selectinload(Resume.resume_data))
            .where(Resume.id == resume_id)
        )
        resume = result.scalar_one_or_none()
        
        if not resume or not resume.resume_data:
            logger.error(f"Resume {resume_id} not found or not parsed")
            return
        
        # Get job
        result = await db.execute(
            select(Job).where(Job.id == job_id)
        )
        job = result.scalar_one_or_none()
        
        if not job:
            logger.error(f"Job {job_id} not found")
            return
        
        logger.info(f"Scoring resume {resume_id} for job {job_id}")
        
        # Prepare resume data for scoring
        resume_data = {
            'skills': resume.resume_data.skills,
            'experience': resume.resume_data.experience,
            'education': resume.resume_data.education,
            'total_experience_years': resume.resume_data.total_experience_years,
            'summary': resume.resume_data.summary
        }
        
        # Prepare job data for scoring
        job_data = {
            'title': job.title,
            'description': job.description,
            'requirements': job.requirements or '',
            'experience_level': job.experience_level or ''
        }
        
        # Calculate score
        score = await scoring_service.score_resume(resume_data, job_data)
        
        # Update resume with score
        resume.score = score
        await db.commit()
        
        logger.info(f"Resume {resume_id} scored: {score}")
        
    except Exception as e:
        logger.error(f"Failed to score resume {resume_id}: {str(e)}")


async def rank_resumes_for_job(job_id: UUID, db: AsyncSession):
    """
    Update rank for all scored resumes in a job.
    
    Args:
        job_id: Job ID
        db: Database session
    """
    try:
        # Get all scored resumes for this job, ordered by score
        result = await db.execute(
            select(Resume)
            .where(
                Resume.job_id == job_id,
                Resume.score.isnot(None)
            )
            .order_by(Resume.score.desc())
        )
        resumes = result.scalars().all()
        
        # Update ranks
        for rank, resume in enumerate(resumes, start=1):
            resume.rank = rank
        
        await db.commit()
        logger.info(f"Updated ranks for {len(resumes)} resumes in job {job_id}")
        
    except Exception as e:
        logger.error(f"Failed to rank resumes for job {job_id}: {str(e)}")


@router.post("/resumes/{resume_id}/score", response_model=dict)
async def score_single_resume(
    resume_id: UUID,
    background_tasks: BackgroundTasks,
    current_user: Annotated[User, Depends(get_current_user)],
    db: Annotated[AsyncSession, Depends(get_db)]
):
    """
    Calculate score for a single resume.
    
    - **resume_id**: Resume ID to score
    
    Requires the resume to be parsed first.
    """
    # Get resume with job and parsed data
    result = await db.execute(
        select(Resume)
        .options(
            selectinload(Resume.job),
            selectinload(Resume.resume_data)
        )
        .where(Resume.id == resume_id)
    )
    resume = result.scalar_one_or_none()
    
    if not resume:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Resume not found"
        )
    
    # Check ownership
    if resume.job.user_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not authorized to score this resume"
        )
    
    # Check if parsed
    if resume.parsing_status != "completed" or not resume.resume_data:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Resume must be parsed before scoring"
        )
    
    # Add to background tasks
    background_tasks.add_task(
        score_resume_background,
        resume_id,
        resume.job_id,
        db
    )
    
    return {
        "message": "Resume scoring started",
        "resume_id": str(resume_id)
    }


@router.post("/jobs/{job_id}/score-all", response_model=dict)
async def score_all_resumes(
    job_id: UUID,
    background_tasks: BackgroundTasks,
    current_user: Annotated[User, Depends(get_current_user)],
    db: Annotated[AsyncSession, Depends(get_db)]
):
    """
    Score all parsed resumes for a job and update rankings.
    
    - **job_id**: Job ID
    
    Scores all resumes with parsing_status='completed' and updates their ranks.
    """
    # Verify job exists and user owns it
    result = await db.execute(
        select(Job).where(Job.id == job_id)
    )
    job = result.scalar_one_or_none()
    
    if not job:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Job not found"
        )
    
    if job.user_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not authorized to score resumes for this job"
        )
    
    # Get all parsed resumes without scores
    result = await db.execute(
        select(Resume)
        .options(selectinload(Resume.resume_data))
        .where(
            Resume.job_id == job_id,
            Resume.parsing_status == "completed",
            Resume.resume_data.has()  # Has parsed data
        )
    )
    parsed_resumes = result.scalars().all()
    
    if not parsed_resumes:
        return {
            "message": "No parsed resumes to score",
            "job_id": str(job_id),
            "count": 0
        }
    
    # Add scoring tasks
    for resume in parsed_resumes:
        background_tasks.add_task(
            score_resume_background,
            resume.id,
            job_id,
            db
        )
    
    # Add ranking task (will run after scoring completes)
    background_tasks.add_task(
        rank_resumes_for_job,
        job_id,
        db
    )
    
    return {
        "message": f"Scoring started for {len(parsed_resumes)} resumes",
        "job_id": str(job_id),
        "count": len(parsed_resumes)
    }


@router.get("/jobs/{job_id}/leaderboard", response_model=list)
async def get_job_leaderboard(
    job_id: UUID,
    current_user: Annotated[User, Depends(get_current_user)],
    db: Annotated[AsyncSession, Depends(get_db)],
    limit: int = 10
):
    """
    Get top-ranked resumes for a job (leaderboard).
    
    - **job_id**: Job ID
    - **limit**: Number of top resumes to return (default: 10)
    
    Returns resumes ordered by score (highest first).
    """
    # Verify job exists and user owns it
    result = await db.execute(
        select(Job).where(Job.id == job_id)
    )
    job = result.scalar_one_or_none()
    
    if not job:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Job not found"
        )
    
    if job.user_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not authorized to access this job's leaderboard"
        )
    
    # Get top resumes
    result = await db.execute(
        select(Resume)
        .where(
            Resume.job_id == job_id,
            Resume.score.isnot(None)
        )
        .order_by(Resume.score.desc())
        .limit(limit)
    )
    top_resumes = result.scalars().all()
    
    # Format response
    leaderboard = []
    for resume in top_resumes:
        leaderboard.append({
            "resume_id": str(resume.id),
            "candidate_name": resume.candidate_name,
            "score": resume.score,
            "rank": resume.rank,
            "file_name": resume.file_name
        })
    
    return leaderboard
