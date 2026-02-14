"""
LangChain-based RAG service: Modern LangChain 1.0+ implementation.
Uses recommended patterns: Direct LLM + Retriever (no legacy chains).
"""
import logging
from typing import List, Dict, Any, Optional
from uuid import UUID

from langchain_core.prompts import ChatPromptTemplate
from langchain_core.documents import Document
from langchain_core.runnables import RunnablePassthrough
from langchain_core.output_parsers import StrOutputParser
from langchain_chroma import Chroma

from app.core.config import settings
from app.core import get_llm, get_embeddings

logger = logging.getLogger(__name__)


class LangChainRAGService:
    """
    Modern RAG service using LangChain 1.0+ recommended patterns.
    
    Uses:
    - Direct LLM invocation (no legacy chains)
    - LCEL (LangChain Expression Language)
    - Runnable interfaces
    """
    
    def __init__(self):
        """Initialize LangChain components with modern APIs."""
        # Use singleton instances (cached)
        self.llm = get_llm(temperature=0.3)
        self.embeddings = get_embeddings()
        
        # Collection name
        self.collection_name = "resume_embeddings"
        
        # Initialize Chroma vector store
        self.vectorstore = Chroma(
            collection_name=self.collection_name,
            embedding_function=self.embeddings,
            persist_directory=settings.VECTOR_STORE_PATH
        )
        
        logger.info("LangChain RAG service initialized (v1.0+ modern pattern)")
    
    def _format_docs(self, docs: List[Document]) -> str:
        """Format documents into a single context string."""
        formatted = []
        for i, doc in enumerate(docs, 1):
            candidate = doc.metadata.get('candidate_name', 'Unknown')
            formatted.append(f"[Resume {i} - {candidate}]\n{doc.page_content}\n")
        return "\n".join(formatted)
    
    async def query_with_retrieval_qa(
        self,
        query: str,
        job_id: Optional[UUID] = None,
        top_k: int = 5
    ) -> Dict[str, Any]:
        """
        Query resumes using modern LCEL pattern.
        
        Modern approach: LLM + Retriever using LCEL.
        
        Args:
            query: Natural language query
            job_id: Optional job ID filter
            top_k: Number of chunks to retrieve
            
        Returns:
            Dictionary with answer and source documents
        """
        try:
            logger.info(f"Processing retrieval query: {query[:100]}...")
            
            # Create retriever with optional filter
            search_kwargs = {"k": top_k}
            if job_id:
                search_kwargs["filter"] = {"job_id": str(job_id)}
            
            retriever = self.vectorstore.as_retriever(
                search_type="similarity",
                search_kwargs=search_kwargs
            )
            
            # Create prompt template
            prompt = ChatPromptTemplate.from_messages([
                ("system", """You are an expert AI recruiter assistant. Use the following resume excerpts to answer the recruiter's question.

Resume excerpts:
{context}

Instructions:
- Answer based ONLY on the provided resume excerpts
- Be specific and cite candidate names when mentioned
- If information isn't in the excerpts, clearly state that
- Provide actionable insights for the recruiter
- Keep your answer concise but informative"""),
                ("human", "{question}")
            ])
            
            # Build LCEL chain (modern pattern)
            # retriever → format docs → prompt → llm → parse output
            rag_chain = (
                {
                    "context": retriever | self._format_docs,
                    "question": RunnablePassthrough()
                }
                | prompt
                | self.llm
                | StrOutputParser()
            )
            
            # Invoke chain
            answer = rag_chain.invoke(query)
            
            # Get source documents separately
            source_docs = retriever.invoke(query)
            
            # Format response
            response = {
                "answer": answer,
                "sources": self._format_sources(source_docs),
                "query": query,
                "num_sources": len(source_docs),
                "chain_type": "LCEL RAG (Modern)"
            }
            
            logger.info("Retrieval query completed successfully")
            return response
            
        except Exception as e:
            logger.error(f"Retrieval query failed: {str(e)}")
            return {
                "answer": f"Error processing query: {str(e)}",
                "sources": [],
                "query": query,
                "num_sources": 0,
                "chain_type": "LCEL RAG (Modern)"
            }
    
    async def query_with_conversational_chain(
        self,
        query: str,
        chat_history: Optional[List[tuple]] = None,
        job_id: Optional[UUID] = None,
        top_k: int = 5
    ) -> Dict[str, Any]:
        """
        Query with conversation history using modern LCEL.
        
        Args:
            query: Natural language query
            chat_history: List of (question, answer) tuples
            job_id: Optional job ID filter
            top_k: Number of chunks to retrieve
            
        Returns:
            Dictionary with answer and source documents
        """
        try:
            logger.info(f"Processing conversational query: {query[:100]}...")
            
            # Create retriever
            search_kwargs = {"k": top_k}
            if job_id:
                search_kwargs["filter"] = {"job_id": str(job_id)}
            
            retriever = self.vectorstore.as_retriever(
                search_type="similarity",
                search_kwargs=search_kwargs
            )
            
            # Format chat history
            history_text = ""
            if chat_history:
                for human_msg, ai_msg in chat_history:
                    history_text += f"Human: {human_msg}\nAssistant: {ai_msg}\n\n"
            
            # Create conversational prompt
            prompt = ChatPromptTemplate.from_messages([
                ("system", """You are an expert AI recruiter assistant having a conversation about candidates.

Use the following resume excerpts and chat history to answer the question.

Resume excerpts:
{context}

Previous conversation:
{chat_history}

Instructions:
- Consider the conversation context
- Answer based on the resume excerpts
- Reference previous questions if relevant
- Be conversational but professional"""),
                ("human", "{question}")
            ])
            
            # Build LCEL chain with history
            rag_chain = (
                {
                    "context": retriever | self._format_docs,
                    "question": RunnablePassthrough(),
                    "chat_history": lambda x: history_text
                }
                | prompt
                | self.llm
                | StrOutputParser()
            )
            
            # Invoke chain
            answer = rag_chain.invoke(query)
            
            # Get source documents
            source_docs = retriever.invoke(query)
            
            # Format response
            response = {
                "answer": answer,
                "sources": self._format_sources(source_docs),
                "query": query,
                "num_sources": len(source_docs),
                "chain_type": "Conversational LCEL (Modern)",
                "chat_history": chat_history or []
            }
            
            logger.info("Conversational query completed successfully")
            return response
            
        except Exception as e:
            logger.error(f"Conversational query failed: {str(e)}")
            return {
                "answer": f"Error processing query: {str(e)}",
                "sources": [],
                "query": query,
                "num_sources": 0,
                "chain_type": "Conversational LCEL (Modern)"
            }
    
    def _format_sources(self, documents: List[Document]) -> List[Dict[str, Any]]:
        """
        Format source documents for response.
        
        Args:
            documents: List of LangChain Document objects
            
        Returns:
            List of formatted source dictionaries
        """
        # Deduplicate by resume_id
        seen_resumes = set()
        sources = []
        
        for doc in documents:
            resume_id = doc.metadata.get("resume_id")
            
            if resume_id and resume_id not in seen_resumes:
                seen_resumes.add(resume_id)
                
                sources.append({
                    "resume_id": resume_id,
                    "candidate_name": doc.metadata.get("candidate_name", "Unknown"),
                    "excerpt": doc.page_content[:200] + "..." if len(doc.page_content) > 200 else doc.page_content,
                    "chunk_index": doc.metadata.get("chunk_index", 0),
                    "metadata": doc.metadata
                })
        
        return sources
    
    async def add_documents_to_vectorstore(
        self,
        resume_id: UUID,
        text_chunks: List[str],
        metadata_list: List[Dict[str, Any]]
    ) -> bool:
        """
        Add documents to LangChain vectorstore.
        
        Args:
            resume_id: Resume UUID
            text_chunks: List of text chunks
            metadata_list: List of metadata dicts
            
        Returns:
            True if successful
        """
        try:
            # Create Document objects
            documents = []
            for i, (text, metadata) in enumerate(zip(text_chunks, metadata_list)):
                doc = Document(
                    page_content=text,
                    metadata={
                        **metadata,
                        "resume_id": str(resume_id),
                        "chunk_index": i
                    }
                )
                documents.append(doc)
            
            # Add to vectorstore
            self.vectorstore.add_documents(documents)
            
            logger.info(f"Added {len(documents)} documents for resume {resume_id}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to add documents: {str(e)}")
            return False
    
    async def delete_documents(self, resume_id: UUID) -> bool:
        """
        Delete documents for a resume.
        
        Args:
            resume_id: Resume UUID
            
        Returns:
            True if successful
        """
        try:
            # Access underlying ChromaDB collection
            collection = self.vectorstore._collection
            
            # Get all IDs for this resume
            results = collection.get(
                where={"resume_id": str(resume_id)}
            )
            
            if results and results.get('ids'):
                collection.delete(ids=results['ids'])
                logger.info(f"Deleted documents for resume {resume_id}")
            
            return True
            
        except Exception as e:
            logger.error(f"Failed to delete documents: {str(e)}")
            return False


# Global instance
langchain_rag_service = LangChainRAGService()