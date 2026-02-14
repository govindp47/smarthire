"""
Singleton instances for LLM and Embeddings.
Prevents re-initialization and improves performance.
"""
from functools import lru_cache

from langchain_openai import ChatOpenAI, OpenAIEmbeddings
from openai import AsyncOpenAI

from app.core.config import settings


@lru_cache(maxsize=1)
def get_embeddings() -> OpenAIEmbeddings:
    """
    Get cached embeddings instance.
    
    Uses LRU cache to avoid re-initialization.
    
    Returns:
        OpenAIEmbeddings instance
    """
    return OpenAIEmbeddings(
        model=settings.EMBEDDING_MODEL,
        api_key=settings.OPENAI_API_KEY
    )


@lru_cache(maxsize=1)
def get_llm(temperature: float = 0.3) -> ChatOpenAI:
    """
    Get cached LLM instance.
    
    Uses LRU cache to avoid re-initialization.
    
    Args:
        temperature: LLM temperature (default: 0.3)
        
    Returns:
        ChatOpenAI instance
    """
    return ChatOpenAI(
        model=settings.OPENAI_MODEL,
        temperature=temperature,
        api_key=settings.OPENAI_API_KEY
    )


@lru_cache(maxsize=1)
def get_parsing_llm() -> ChatOpenAI:
    """
    Get LLM instance for resume parsing.
    
    Uses lower temperature for factual extraction.
    
    Returns:
        ChatOpenAI instance optimized for parsing
    """
    return ChatOpenAI(
        model=settings.OPENAI_MODEL,
        temperature=0.1,  # Very low for structured extraction
        api_key=settings.OPENAI_API_KEY
    )


@lru_cache(maxsize=1)
def get_openai_client() -> AsyncOpenAI:
    """
    Get cached OpenAI client (for direct API calls).
    
    Used by services that need OpenAI client directly
    (not LangChain wrapper).
    
    Returns:
        AsyncOpenAI instance
    """
    return AsyncOpenAI(api_key=settings.OPENAI_API_KEY)
