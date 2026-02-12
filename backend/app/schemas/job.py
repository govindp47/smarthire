"""
Pydantic schemas for Job model.
"""
from datetime import datetime
from typing import Optional
from uuid import UUID

from pydantic import BaseModel, Field, ConfigDict


# Base schema with common fields
class JobBase(BaseModel):
    """Base job schema."""
    title: str = Field(..., min_length=1, max_length=255)
    description: str = Field(..., min_length=1)
    requirements: Optional[str] = None
    location: Optional[str] = Field(None, max_length=255)
    employment_type: Optional[str] = Field(None, max_length=50)  # Full-time, Contract, etc
    experience_level: Optional[str] = Field(None, max_length=50)  # Junior, Mid, Senior
    salary_range: Optional[str] = Field(None, max_length=100)


# Schema for job creation
class JobCreate(JobBase):
    """Schema for creating a new job."""
    status: Optional[str] = Field("draft", max_length=50)  # open, closed, draft


# Schema for job update
class JobUpdate(BaseModel):
    """Schema for updating a job."""
    title: Optional[str] = Field(None, min_length=1, max_length=255)
    description: Optional[str] = Field(None, min_length=1)
    requirements: Optional[str] = None
    location: Optional[str] = Field(None, max_length=255)
    employment_type: Optional[str] = Field(None, max_length=50)
    experience_level: Optional[str] = Field(None, max_length=50)
    salary_range: Optional[str] = Field(None, max_length=100)
    status: Optional[str] = Field(None, max_length=50)


# Schema for job in response
class Job(JobBase):
    """Schema for job in response."""
    id: UUID
    user_id: UUID
    status: str
    created_at: datetime
    updated_at: datetime
    
    model_config = ConfigDict(from_attributes=True)


# Schema for job list (minimal data)
class JobList(BaseModel):
    """Schema for job in list view."""
    id: UUID
    title: str
    location: Optional[str]
    employment_type: Optional[str]
    status: str
    created_at: datetime
    
    model_config = ConfigDict(from_attributes=True)
