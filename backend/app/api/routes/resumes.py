"""
Resume management routes: upload, list, get, delete.
"""
from typing import Annotated, List
from uuid import UUID

from fastapi import (
    APIRouter, Depends, HTTPException, status, 
    UploadFile, File, Query
)
from fastapi.responses import StreamingResponse
from sqlalchemy import select, desc
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.database import get_db
from app.models import Resume, Job, User, ResumeData
from app.schemas import (
    Resume as ResumeSchema, 
    ResumeList, 
    ResumeWithData,
    FileUploadResponse
)
from app.api.deps import get_current_user
from app.services.file_storage import file_storage
import io

router = APIRouter()


@router.post("/{job_id}/resumes", response_model=FileUploadResponse, status_code=status.HTTP_201_CREATED)
async def upload_resume(
    job_id: UUID,
    current_user: Annotated[User, Depends(get_current_user)],
    db: Annotated[AsyncSession, Depends(get_db)],
    file: UploadFile = File(...)
):
    """
    Upload a resume for a job posting.
    
    - **job_id**: Job ID to associate resume with
    - **file**: Resume file (PDF or DOCX, max 5MB)
    
    Returns upload confirmation with resume ID.
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
            detail="Not authorized to upload resumes to this job"
        )
    
    # Save file to storage
    file_info = await file_storage.save_file(file, str(job_id))
    
    # Create resume record
    new_resume = Resume(
        job_id=job_id,
        file_name=file_info["file_name"],
        file_path=file_info["file_path"],
        file_size=file_info["file_size"],
        file_type=file_info["file_type"],
        upload_status="uploaded",
        parsing_status="pending"
    )
    
    db.add(new_resume)
    await db.commit()
    await db.refresh(new_resume)
    
    return FileUploadResponse(
        message="Resume uploaded successfully",
        resume_id=new_resume.id,
        file_name=new_resume.file_name,
        file_size=new_resume.file_size,
        status="uploaded"
    )


@router.get("/{job_id}/resumes", response_model=List[ResumeList])
async def list_resumes(
    job_id: UUID,
    current_user: Annotated[User, Depends(get_current_user)],
    db: Annotated[AsyncSession, Depends(get_db)],
    parsing_status: str | None = Query(None, description="Filter by parsing status"),
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=100)
):
    """
    List all resumes for a job.
    
    - **job_id**: Job ID
    - **parsing_status**: Filter by status (pending, processing, completed, failed)
    - **skip**: Pagination offset
    - **limit**: Number of results
    
    Returns resumes ordered by score (highest first), then by upload date.
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
            detail="Not authorized to access this job's resumes"
        )
    
    # Build query
    query = select(Resume).where(Resume.job_id == job_id)
    
    # Apply parsing status filter if provided
    if parsing_status:
        if parsing_status not in ["pending", "processing", "completed", "failed"]:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid parsing status"
            )
        query = query.where(Resume.parsing_status == parsing_status)
    
    # Order by score (desc, nulls last) then by created_at (desc)
    query = query.order_by(
        Resume.score.desc().nulls_last(),
        desc(Resume.created_at)
    ).offset(skip).limit(limit)
    
    # Execute query
    result = await db.execute(query)
    resumes = result.scalars().all()
    
    return resumes


@router.get("/resumes/{resume_id}", response_model=ResumeWithData)
async def get_resume(
    resume_id: UUID,
    current_user: Annotated[User, Depends(get_current_user)],
    db: Annotated[AsyncSession, Depends(get_db)]
):
    """
    Get detailed resume information including parsed data.
    
    Returns resume with parsed data if available.
    """
    # Get resume with job and parsed data
    result = await db.execute(
        select(Resume)
        .options(selectinload(Resume.job), selectinload(Resume.resume_data))
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
    
    return resume


@router.get("/resumes/{resume_id}/download")
async def download_resume(
    resume_id: UUID,
    current_user: Annotated[User, Depends(get_current_user)],
    db: Annotated[AsyncSession, Depends(get_db)]
):
    """
    Download the original resume file.
    
    Returns the file as a downloadable attachment.
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
            detail="Not authorized to download this resume"
        )
    
    # Get file from storage
    file_content = await file_storage.get_file(resume.file_path)
    
    # Determine media type
    media_type = "application/pdf" if resume.file_type == "pdf" else "application/vnd.openxmlformats-officedocument.wordprocessingml.document"
    
    # Return file as streaming response
    return StreamingResponse(
        io.BytesIO(file_content),
        media_type=media_type,
        headers={
            "Content-Disposition": f'attachment; filename="{resume.file_name}"'
        }
    )


@router.delete("/resumes/{resume_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_resume(
    resume_id: UUID,
    current_user: Annotated[User, Depends(get_current_user)],
    db: Annotated[AsyncSession, Depends(get_db)]
):
    """
    Delete a resume.
    
    Deletes both the database record and the file from storage.
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
            detail="Not authorized to delete this resume"
        )
    
    # Delete file from storage
    await file_storage.delete_file(resume.file_path)
    
    # Delete from database (cascades to resume_data and embeddings)
    await db.delete(resume)
    await db.commit()
    
    return None