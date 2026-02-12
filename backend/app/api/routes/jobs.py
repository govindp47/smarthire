"""
Job management routes: CRUD operations.
"""
from typing import Annotated, List
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy import select, desc
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.models import Job, User
from app.schemas import Job as JobSchema, JobCreate, JobUpdate, JobList
from app.api.deps import get_current_user

router = APIRouter()


@router.post("", response_model=JobSchema, status_code=status.HTTP_201_CREATED)
async def create_job(
    job_data: JobCreate,
    current_user: Annotated[User, Depends(get_current_user)],
    db: Annotated[AsyncSession, Depends(get_db)]
):
    """
    Create a new job posting.
    
    - **title**: Job title (required)
    - **description**: Full job description (required)
    - **requirements**: Skills/qualifications (optional)
    - **location**: Job location (optional)
    - **employment_type**: Full-time, Contract, etc (optional)
    - **experience_level**: Junior, Mid, Senior (optional)
    - **salary_range**: Compensation info (optional)
    - **status**: open, closed, draft (default: draft)
    
    Requires authentication.
    """
    # Validate status
    if job_data.status not in ["open", "closed", "draft"]:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Status must be 'open', 'closed', or 'draft'"
        )
    
    # Create new job
    new_job = Job(
        user_id=current_user.id,
        title=job_data.title,
        description=job_data.description,
        requirements=job_data.requirements,
        location=job_data.location,
        employment_type=job_data.employment_type,
        experience_level=job_data.experience_level,
        salary_range=job_data.salary_range,
        status=job_data.status,
    )
    
    db.add(new_job)
    await db.commit()
    await db.refresh(new_job)
    
    return new_job


@router.get("", response_model=List[JobList])
async def list_jobs(
    current_user: Annotated[User, Depends(get_current_user)],
    db: Annotated[AsyncSession, Depends(get_db)],
    status_filter: str | None = Query(None, description="Filter by status: open, closed, draft"),
    skip: int = Query(0, ge=0, description="Number of records to skip"),
    limit: int = Query(100, ge=1, le=100, description="Number of records to return")
):
    """
    Get all jobs for the current user.
    
    - **status_filter**: Filter by job status (optional)
    - **skip**: Pagination offset (default: 0)
    - **limit**: Number of results (default: 100, max: 100)
    
    Returns list of jobs ordered by creation date (newest first).
    """
    # Build query
    query = select(Job).where(Job.user_id == current_user.id)
    
    # Apply status filter if provided
    if status_filter:
        if status_filter not in ["open", "closed", "draft"]:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Status must be 'open', 'closed', or 'draft'"
            )
        query = query.where(Job.status == status_filter)
    
    # Apply ordering and pagination
    query = query.order_by(desc(Job.created_at)).offset(skip).limit(limit)
    
    # Execute query
    result = await db.execute(query)
    jobs = result.scalars().all()
    
    return jobs


@router.get("/{job_id}", response_model=JobSchema)
async def get_job(
    job_id: UUID,
    current_user: Annotated[User, Depends(get_current_user)],
    db: Annotated[AsyncSession, Depends(get_db)]
):
    """
    Get a specific job by ID.
    
    Returns full job details.
    Only the job owner can access.
    """
    # Get job
    result = await db.execute(
        select(Job).where(Job.id == job_id)
    )
    job = result.scalar_one_or_none()
    
    # Check if job exists
    if not job:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Job not found"
        )
    
    # Check ownership
    if job.user_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not authorized to access this job"
        )
    
    return job


@router.put("/{job_id}", response_model=JobSchema)
async def update_job(
    job_id: UUID,
    job_data: JobUpdate,
    current_user: Annotated[User, Depends(get_current_user)],
    db: Annotated[AsyncSession, Depends(get_db)]
):
    """
    Update a job posting.
    
    Only the job owner can update.
    Provide only the fields you want to update.
    """
    # Get job
    result = await db.execute(
        select(Job).where(Job.id == job_id)
    )
    job = result.scalar_one_or_none()
    
    # Check if job exists
    if not job:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Job not found"
        )
    
    # Check ownership
    if job.user_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not authorized to update this job"
        )
    
    # Validate status if provided
    if job_data.status and job_data.status not in ["open", "closed", "draft"]:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Status must be 'open', 'closed', or 'draft'"
        )
    
    # Update fields (only if provided)
    update_data = job_data.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(job, field, value)
    
    await db.commit()
    await db.refresh(job)
    
    return job


@router.delete("/{job_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_job(
    job_id: UUID,
    current_user: Annotated[User, Depends(get_current_user)],
    db: Annotated[AsyncSession, Depends(get_db)]
):
    """
    Delete a job posting.
    
    Only the job owner can delete.
    This will also delete all associated resumes (cascade).
    """
    # Get job
    result = await db.execute(
        select(Job).where(Job.id == job_id)
    )
    job = result.scalar_one_or_none()
    
    # Check if job exists
    if not job:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Job not found"
        )
    
    # Check ownership
    if job.user_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not authorized to delete this job"
        )
    
    # Delete job (cascades to resumes)
    await db.delete(job)
    await db.commit()
    
    return None


@router.get("/{job_id}/stats", response_model=dict)
async def get_job_stats(
    job_id: UUID,
    current_user: Annotated[User, Depends(get_current_user)],
    db: Annotated[AsyncSession, Depends(get_db)]
):
    """
    Get statistics for a job posting.
    
    Returns:
    - Total resumes
    - Parsed resumes
    - Pending resumes
    - Average score
    """
    # Get job
    result = await db.execute(
        select(Job).where(Job.id == job_id)
    )
    job = result.scalar_one_or_none()
    
    # Check if job exists
    if not job:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Job not found"
        )
    
    # Check ownership
    if job.user_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not authorized to access this job"
        )
    
    # Import Resume model here to avoid circular import
    from app.models import Resume
    from sqlalchemy import func
    
    # Get resume statistics
    stats_query = select(
        func.count(Resume.id).label("total_resumes"),
        func.count(Resume.id).filter(Resume.parsing_status == "completed").label("parsed_resumes"),
        func.count(Resume.id).filter(Resume.parsing_status == "pending").label("pending_resumes"),
        func.avg(Resume.score).label("average_score")
    ).where(Resume.job_id == job_id)
    
    stats_result = await db.execute(stats_query)
    stats = stats_result.one()
    
    return {
        "job_id": str(job_id),
        "job_title": job.title,
        "total_resumes": stats.total_resumes or 0,
        "parsed_resumes": stats.parsed_resumes or 0,
        "pending_resumes": stats.pending_resumes or 0,
        "average_score": round(float(stats.average_score or 0), 2)
    }
