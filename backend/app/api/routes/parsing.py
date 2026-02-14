"""
Resume parsing routes: Parse and extract structured data from resumes.
"""
import logging
from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status, BackgroundTasks
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.database import get_db
from app.models import Resume, Job, User, ResumeData
from app.schemas import Resume as ResumeSchema, ResumeWithData
from app.api.deps import get_current_user
from app.services.text_extraction import text_extractor
from app.services.rag_langchain import langchain_rag_service
from app.services.resume_parser import resume_parser

logger = logging.getLogger(__name__)
router = APIRouter()


async def parse_resume_background(resume_id: UUID, db: AsyncSession):
    """
    Background task to parse resume.
    
    Args:
        resume_id: Resume ID to parse
        db: Database session
    """
    try:
        # Get resume
        result = await db.execute(
            select(Resume).where(Resume.id == resume_id)
        )
        resume = result.scalar_one_or_none()
        
        if not resume:
            logger.error(f"Resume {resume_id} not found for parsing")
            return
        
        # Update status to processing
        resume.parsing_status = "processing"
        await db.commit()
        
        logger.info(f"Starting to parse resume {resume_id}")
        
        # Get file content from storage (works for both local and S3)
        from app.services.file_storage import file_storage
        file_content = await file_storage.get_file(resume.file_path)
        
        # Extract text from file content bytes
        raw_text = await text_extractor.extract_text_from_bytes(
            file_content, 
            resume.file_type
        )
        
        # Parse with LLM
        parsed_data = await resume_parser.parse_resume(raw_text)
        
        # Update resume with extracted candidate info
        if parsed_data.get("candidate_name"):
            resume.candidate_name = parsed_data["candidate_name"]
        if parsed_data.get("candidate_email"):
            resume.candidate_email = parsed_data["candidate_email"]
        
        # Create or update resume_data
        result = await db.execute(
            select(ResumeData).where(ResumeData.resume_id == resume_id)
        )
        resume_data = result.scalar_one_or_none()
        
        if resume_data:
            # Update existing
            resume_data.raw_text = raw_text
            resume_data.skills = parsed_data.get("skills", [])
            resume_data.experience = parsed_data.get("experience", [])
            resume_data.education = parsed_data.get("education", [])
            resume_data.certifications = parsed_data.get("certifications", [])
            resume_data.languages = parsed_data.get("languages", [])
            resume_data.total_experience_years = parsed_data.get("total_experience_years")
            resume_data.summary = parsed_data.get("summary")
            resume_data.metadata = parsed_data.get("metadata", {})
        else:
            # Create new
            resume_data = ResumeData(
                resume_id=resume_id,
                raw_text=raw_text,
                skills=parsed_data.get("skills", []),
                experience=parsed_data.get("experience", []),
                education=parsed_data.get("education", []),
                certifications=parsed_data.get("certifications", []),
                languages=parsed_data.get("languages", []),
                total_experience_years=parsed_data.get("total_experience_years"),
                summary=parsed_data.get("summary"),
                metadata=parsed_data.get("metadata", {})
            )
            db.add(resume_data)
        
        # Update resume status
        resume.parsing_status = "completed"
        
        await db.commit()
        logger.info(f"Successfully parsed resume {resume_id}")

        # Create embeddings for RAG using LangChain (don't fail if this errors)
        try:
            # Chunk the text
            chunks = text_extractor.chunk_text(raw_text, chunk_size=1000, overlap=100)
            
            # Add metadata to chunks
            metadata_list = []
            for i, chunk in enumerate(chunks):
                metadata_list.append({
                    "candidate_name": resume.candidate_name or "Unknown",
                    "job_id": str(resume.job_id),
                    "chunk_index": i,
                    "total_chunks": len(chunks)
                })
            
            # Store in vector database using LangChain
            success = await langchain_rag_service.add_documents_to_vectorstore(
                resume_id=resume_id,
                text_chunks=chunks,
                metadata_list=metadata_list
            )
            
            if success:
                logger.info(f"Created {len(chunks)} embeddings for resume {resume_id} using LangChain")
            
        except Exception as e:
            logger.warning(f"Failed to create embeddings for resume {resume_id}: {str(e)}")
            # Don't fail the whole parsing if embeddings fail
        
    except Exception as e:
        logger.error(f"Failed to parse resume {resume_id}: {str(e)}")
        
        # Update status to failed
        try:
            result = await db.execute(
                select(Resume).where(Resume.id == resume_id)
            )
            resume = result.scalar_one_or_none()
            if resume:
                resume.parsing_status = "failed"
                await db.commit()
        except:
            pass


@router.post("/resumes/{resume_id}/parse", response_model=dict)
async def trigger_resume_parsing(
    resume_id: UUID,
    background_tasks: BackgroundTasks,
    current_user: Annotated[User, Depends(get_current_user)],
    db: Annotated[AsyncSession, Depends(get_db)]
):
    """
    Trigger resume parsing (async background task).
    
    - **resume_id**: Resume ID to parse
    
    Returns immediately while parsing happens in background.
    """
    # Get resume with job
    result = await db.execute(
        select(Resume)
        .options(selectinload(Resume.job))
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
            detail="Not authorized to parse this resume"
        )
    
    # Check if already parsed
    if resume.parsing_status == "completed":
        return {
            "message": "Resume already parsed",
            "resume_id": str(resume_id),
            "status": "completed"
        }
    
    # Check if currently processing
    if resume.parsing_status == "processing":
        return {
            "message": "Resume is currently being parsed",
            "resume_id": str(resume_id),
            "status": "processing"
        }
    
    # Add to background tasks
    background_tasks.add_task(parse_resume_background, resume_id, db)
    
    return {
        "message": "Resume parsing started",
        "resume_id": str(resume_id),
        "status": "processing"
    }


@router.post("/jobs/{job_id}/parse-all", response_model=dict)
async def parse_all_resumes(
    job_id: UUID,
    background_tasks: BackgroundTasks,
    current_user: Annotated[User, Depends(get_current_user)],
    db: Annotated[AsyncSession, Depends(get_db)]
):
    """
    Parse all pending resumes for a job.
    
    - **job_id**: Job ID
    
    Triggers parsing for all resumes with status 'pending'.
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
            detail="Not authorized to parse resumes for this job"
        )
    
    # Get all pending resumes
    result = await db.execute(
        select(Resume).where(
            Resume.job_id == job_id,
            Resume.parsing_status == "pending"
        )
    )
    pending_resumes = result.scalars().all()
    
    if not pending_resumes:
        return {
            "message": "No pending resumes to parse",
            "job_id": str(job_id),
            "count": 0
        }
    
    # Add all to background tasks
    for resume in pending_resumes:
        background_tasks.add_task(parse_resume_background, resume.id, db)
    
    return {
        "message": f"Parsing started for {len(pending_resumes)} resumes",
        "job_id": str(job_id),
        "count": len(pending_resumes)
    }


@router.get("/resumes/{resume_id}/parsed-data", response_model=ResumeWithData)
async def get_parsed_resume_data(
    resume_id: UUID,
    current_user: Annotated[User, Depends(get_current_user)],
    db: Annotated[AsyncSession, Depends(get_db)]
):
    """
    Get parsed resume data.
    
    Returns resume with full parsed data if available.
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
            detail="Not authorized to access this resume"
        )
    
    if resume.parsing_status != "completed":
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Resume parsing not completed. Current status: {resume.parsing_status}"
        )
    
    return resume