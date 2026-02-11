"""
Resume model and related tables.
"""
from uuid import uuid4

from sqlalchemy import (
    Column, DateTime, Float, ForeignKey, Integer, 
    String, Text, CheckConstraint, func
)
from sqlalchemy.dialects.postgresql import UUID, JSONB
from sqlalchemy.orm import relationship

from app.database import Base


class Resume(Base):
    """Uploaded candidate resume."""
    
    __tablename__ = "resumes"
    
    # Primary Key
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid4, index=True)
    
    # Foreign Key
    job_id = Column(UUID(as_uuid=True), ForeignKey("jobs.id", ondelete="CASCADE"), nullable=False, index=True)
    
    # Candidate Info (extracted)
    candidate_name = Column(String(255), nullable=True)
    candidate_email = Column(String(255), nullable=True)
    
    # File Info
    file_name = Column(String(255), nullable=False)
    file_path = Column(Text, nullable=False)  # S3 path or local path
    file_size = Column(Integer, nullable=False)
    file_type = Column(String(10), nullable=False)  # pdf, docx
    
    # Processing Status
    upload_status = Column(String(50), default="uploaded", nullable=False)
    parsing_status = Column(String(50), default="pending", nullable=False, index=True)
    
    # Scoring
    score = Column(Float, nullable=True, index=True)  # 0-100
    rank = Column(Integer, nullable=True)  # Position in ranking
    
    # Timestamps
    created_at = Column(DateTime(timezone=True), default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), default=func.now(), onupdate=func.now(), nullable=False)

    # Relationships
    job = relationship("Job", back_populates="resumes")
    resume_data = relationship("ResumeData", back_populates="resume", uselist=False, cascade="all, delete-orphan")
    embeddings = relationship("ResumeEmbedding", back_populates="resume", cascade="all, delete-orphan")
    
    # Constraints
    __table_args__ = (
        CheckConstraint("file_type IN ('pdf', 'docx')", name="check_file_type"),
        CheckConstraint(
            "parsing_status IN ('pending', 'processing', 'completed', 'failed')", 
            name="check_parsing_status"
        ),
        CheckConstraint("score >= 0 AND score <= 100", name="check_score_range"),
    )
    
    def __repr__(self):
        return f"<Resume(candidate={self.candidate_name}, score={self.score})>"


class ResumeData(Base):
    """Structured data extracted from resume."""
    
    __tablename__ = "resume_data"
    
    # Primary Key
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid4, index=True)
    
    # Foreign Key (one-to-one)
    resume_id = Column(
        UUID(as_uuid=True), 
        ForeignKey("resumes.id", ondelete="CASCADE"), 
        unique=True, 
        nullable=False,
        index=True
    )
    
    # Extracted Data
    raw_text = Column(Text, nullable=True)
    skills = Column(JSONB, default=list, nullable=False)  # ["Python", "FastAPI", ...]
    experience = Column(JSONB, default=list, nullable=False)  # [{title, company, ...}, ...]
    education = Column(JSONB, default=list, nullable=False)  # [{degree, institution, ...}, ...]
    certifications = Column(JSONB, default=list, nullable=False)
    languages = Column(JSONB, default=list, nullable=False)
    
    # Computed Fields
    total_experience_years = Column(Float, nullable=True, index=True)
    summary = Column(Text, nullable=True)  # AI-generated summary
    
    # Metadata
    resume_metadata = Column(JSONB, default=dict, nullable=False)
    
    # Timestamps
    created_at = Column(DateTime(timezone=True), default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), default=func.now(), onupdate=func.now(), nullable=False)

    # Relationships
    resume = relationship("Resume", back_populates="resume_data")
    
    def __repr__(self):
        return f"<ResumeData(resume_id={self.resume_id}, skills_count={len(self.skills or [])})>"


class ResumeEmbedding(Base):
    """Vector embeddings for RAG (ChromaDB references)."""
    
    __tablename__ = "resume_embeddings"
    
    # Primary Key
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid4, index=True)
    
    # Foreign Key
    resume_id = Column(
        UUID(as_uuid=True), 
        ForeignKey("resumes.id", ondelete="CASCADE"), 
        nullable=False,
        index=True
    )
    
    # ChromaDB Reference
    chroma_id = Column(String(255), unique=True, nullable=False, index=True)
    
    # Chunk Info
    chunk_text = Column(Text, nullable=False)
    chunk_index = Column(Integer, nullable=False)
    
    # Metadata
    embedding_metadata = Column(JSONB, default=dict, nullable=False)
    
    # Timestamps
    created_at = Column(DateTime(timezone=True), default=func.now(), nullable=False)

    # Relationships
    resume = relationship("Resume", back_populates="embeddings")
    
    def __repr__(self):
        return f"<ResumeEmbedding(chroma_id={self.chroma_id}, chunk_index={self.chunk_index})>"
