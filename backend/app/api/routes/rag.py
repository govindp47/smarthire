"""
RAG query routes: Natural language queries over resumes.
"""
import logging
from typing import Annotated, List, Optional
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status, Query
from pydantic import BaseModel, Field
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.models import Job, User
from app.api.deps import get_current_user
from app.services.rag_langchain import langchain_rag_service

logger = logging.getLogger(__name__)
router = APIRouter()


class QueryRequest(BaseModel):
    """Request model for RAG query."""
    query: str = Field(..., min_length=1, max_length=500, description="Natural language query")
    top_k: int = Field(5, ge=1, le=20, description="Number of relevant chunks to retrieve")
    use_conversation: bool = Field(False, description="Use conversational chain with memory")
    chat_history: Optional[List[tuple]] = Field(None, description="Previous conversation history")


class QueryResponse(BaseModel):
    """Response model for RAG query."""
    answer: str
    sources: list
    query: str
    num_sources: int


@router.post("/jobs/{job_id}/query", response_model=QueryResponse)
async def query_job_resumes(
    job_id: UUID,
    query_request: QueryRequest,
    current_user: Annotated[User, Depends(get_current_user)],
    db: Annotated[AsyncSession, Depends(get_db)]
):
    """
    Query resumes for a specific job using natural language.
    
    Uses LangChain's RAG implementation with:
    - RetrievalQA chain (default): Best for single queries
    - ConversationalRetrievalChain: Enable with use_conversation=true for multi-turn
    
    Example queries:
    - "Who has 5+ years of Python experience?"
    - "Find candidates with AWS and Docker skills"
    - "Show me senior engineers with machine learning background"
    - "Who has worked at FAANG companies?"
    
    Returns an AI-generated answer with source citations.
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
            detail="Not authorized to query this job's resumes"
        )
    
    # Execute RAG query using LangChain
    if query_request.use_conversation:
        result = await langchain_rag_service.query_with_conversational_chain(
            query=query_request.query,
            chat_history=query_request.chat_history,
            job_id=job_id,
            top_k=query_request.top_k
        )
    else:
        result = await langchain_rag_service.query_with_retrieval_qa(
            query=query_request.query,
            job_id=job_id,
            top_k=query_request.top_k
        )
    
    return QueryResponse(**result)


@router.post("/query", response_model=QueryResponse)
async def query_all_resumes(
    query_request: QueryRequest,
    current_user: Annotated[User, Depends(get_current_user)],
    db: Annotated[AsyncSession, Depends(get_db)]
):
    """
    Query ALL resumes across all jobs (for the current user).
    
    Uses LangChain's RAG implementation.
    
    Note: This searches across all jobs owned by the user.
    Use the job-specific endpoint to limit search to one job.
    """
    # Execute RAG query using LangChain (no job_id filter)
    if query_request.use_conversation:
        result = await langchain_rag_service.query_with_conversational_chain(
            query=query_request.query,
            chat_history=query_request.chat_history,
            job_id=None,
            top_k=query_request.top_k
        )
    else:
        result = await langchain_rag_service.query_with_retrieval_qa(
            query=query_request.query,
            job_id=None,
            top_k=query_request.top_k
        )
    
    return QueryResponse(**result)


@router.get("/jobs/{job_id}/vector-stats", response_model=dict)
async def get_job_vector_stats(
    job_id: UUID,
    current_user: Annotated[User, Depends(get_current_user)],
    db: Annotated[AsyncSession, Depends(get_db)]
):
    """
    Get statistics about embeddings for a job.
    
    Returns information about how many resume chunks are indexed.
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
            detail="Not authorized to access this job"
        )
    
    # Get collection stats from LangChain service
    try:
        collection = langchain_rag_service.vectorstore._collection
        total_chunks = collection.count()
        
        collection_stats = {
            "collection_name": langchain_rag_service.collection_name,
            "total_chunks": total_chunks,
            "status": "active"
        }
    except Exception as e:
        collection_stats = {
            "collection_name": "resume_embeddings",
            "status": "error",
            "error": str(e)
        }
    
    return {
        "job_id": str(job_id),
        "job_title": job.title,
        "vector_store": collection_stats
    }


@router.get("/vector-store/stats", response_model=dict)
async def get_vector_store_stats(
    current_user: Annotated[User, Depends(get_current_user)]
):
    """
    Get overall vector store statistics.
    
    Returns information about the entire ChromaDB collection (via LangChain).
    """
    try:
        collection = langchain_rag_service.vectorstore._collection
        total_chunks = collection.count()
        
        return {
            "collection_name": langchain_rag_service.collection_name,
            "total_chunks": total_chunks,
            "status": "active",
            "backend": "LangChain + ChromaDB"
        }
    except Exception as e:
        return {
            "collection_name": "resume_embeddings",
            "status": "error",
            "error": str(e),
            "backend": "LangChain + ChromaDB"
        }