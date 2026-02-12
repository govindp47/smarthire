"""
Pydantic schemas for Resume model.
"""
from datetime import datetime
from typing import Optional, List, Dict, Any
from uuid import UUID

from pydantic import BaseModel, Field, ConfigDict


# Base schema
class ResumeBase(BaseModel):
    """Base resume schema."""
    candidate_name: Optional[str] = None
    candidate_email: Optional[str] = None


# Schema for resume creation (file upload response)
class ResumeCreate(ResumeBase):
    """Schema for creating a resume (internal use)."""
    job_id: UUID
    file_name: str
    file_path: str
    file_size: int
    file_type: str


# Schema for resume in response
class Resume(ResumeBase):
    """Schema for resume in response."""
    id: UUID
    job_id: UUID
    file_name: str
    file_size: int
    file_type: str
    upload_status: str
    parsing_status: str
    score: Optional[float] = None
    rank: Optional[int] = None
    created_at: datetime
    updated_at: datetime
    
    model_config = ConfigDict(from_attributes=True)


# Schema for resume list (minimal data)
class ResumeList(BaseModel):
    """Schema for resume in list view."""
    id: UUID
    candidate_name: Optional[str]
    file_name: str
    parsing_status: str
    score: Optional[float]
    rank: Optional[int]
    created_at: datetime
    
    model_config = ConfigDict(from_attributes=True)


# Schema for resume with parsed data
class ResumeWithData(Resume):
    """Schema for resume with parsed data included."""
    resume_data: Optional["ResumeDataSchema"] = None
    
    model_config = ConfigDict(from_attributes=True)


# Schema for parsed resume data
class ResumeDataSchema(BaseModel):
    """Schema for parsed resume data."""
    id: UUID
    resume_id: UUID
    raw_text: Optional[str] = None
    skills: List[str] = Field(default_factory=list)
    experience: List[Dict[str, Any]] = Field(default_factory=list)
    education: List[Dict[str, Any]] = Field(default_factory=list)
    certifications: List[str] = Field(default_factory=list)
    languages: List[str] = Field(default_factory=list)
    total_experience_years: Optional[float] = None
    summary: Optional[str] = None
    metadata: Dict[str, Any] = Field(default_factory=dict)
    created_at: datetime
    updated_at: datetime
    
    model_config = ConfigDict(from_attributes=True)


# Schema for file upload response
class FileUploadResponse(BaseModel):
    """Response after file upload."""
    message: str
    resume_id: UUID
    file_name: str
    file_size: int
    status: str
