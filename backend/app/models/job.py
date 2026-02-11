"""
Job posting model.
"""
from uuid import uuid4

from sqlalchemy import Column, DateTime, ForeignKey, String, Text, CheckConstraint, func
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship

from app.database import Base


class Job(Base):
    """Job posting model."""
    
    __tablename__ = "jobs"
    
    # Primary Key
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid4, index=True)
    
    # Foreign Key
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    
    # Job Details
    title = Column(String(255), nullable=False)
    description = Column(Text, nullable=False)
    requirements = Column(Text, nullable=True)
    location = Column(String(255), nullable=True)
    employment_type = Column(String(50), nullable=True)  # Full-time, Contract, etc.
    experience_level = Column(String(50), nullable=True)  # Junior, Mid, Senior
    salary_range = Column(String(100), nullable=True)
    
    # Status
    status = Column(String(50), default="open", nullable=False, index=True)
    
    # Timestamps
    created_at = Column(DateTime(timezone=True), default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), default=func.now(), onupdate=func.now(), nullable=False)

    # Relationships
    owner = relationship("User", back_populates="jobs")
    resumes = relationship("Resume", back_populates="job", cascade="all, delete-orphan")
    
    # Constraints
    __table_args__ = (
        CheckConstraint("status IN ('open', 'closed', 'draft')", name="check_job_status"),
    )
    
    def __repr__(self):
        return f"<Job(title={self.title}, status={self.status})>"
