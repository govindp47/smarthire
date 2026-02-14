# SmartHire - Architecture Documentation

**Last Updated:** 2026-02-15  
**Version:** 1.0.0

---

## System Architecture

```
┌─────────────────┐
│  React Frontend  │
│  (Vite + React)  │
└────────┬────────┘
         │ HTTP/REST
         ▼
┌─────────────────┐
│  FastAPI Backend │
│  (Python 3.11+)  │
└────────┬────────┘
         │
         ├──────────┐
         │          │
         ▼          ▼
┌──────────┐  ┌──────────┐
│PostgreSQL│  │ ChromaDB │
│  (Main)  │  │ (Vector) │
└──────────┘  └──────────┘
         │          │
         └────┬─────┘
              ▼
         ┌──────────┐
         │ OpenAI   │
         │   API    │
         └──────────┘
```

---

## LangChain 1.0+ Integration

### **Modern LCEL Architecture**

SmartHire uses **LangChain 1.0+ with LCEL (LangChain Expression Language)** - the modern, recommended approach.

**Key Components:**

1. **LangChain Core**
   - `ChatPromptTemplate` - Modern chat prompts
   - `RunnablePassthrough` - Data flow
   - `StrOutputParser` - Parse LLM output
   - LCEL chains (composable pipelines)

2. **LangChain OpenAI**
   - `ChatOpenAI` - LLM interface (GPT-4o-mini)
   - `OpenAIEmbeddings` - text-embedding-ada-002

3. **LangChain Chroma**
   - `Chroma` - Vector store with native LangChain integration

**Why LCEL?**

- ✅ Modern recommended pattern (no legacy chains)
- ✅ More composable and debuggable
- ✅ Better streaming support
- ✅ Clearer data flow

---

## RAG Pipeline Architecture

### **Phase 1: Document Ingestion**

```
Resume Upload (PDF/DOCX)
      ↓
Text Extraction (pypdf/python-docx)
      ↓
LLM Parsing (GPT-4o-mini, JSON mode)
  → Extract: skills, experience, education
  → Save structured data to PostgreSQL
      ↓
Text Chunking (1000 chars, 100 overlap)
      ↓
Generate Embeddings (text-embedding-ada-002)
      ↓
Store in ChromaDB via LangChain Document objects
```

**Services:**

- `text_extraction.py` - PDF/DOCX parsing
- `resume_parser.py` - LLM structured extraction
- `rag_langchain.py` - Embedding + vector storage

---

### **Phase 2: Query Processing**

#### **Modern LCEL RAG Pattern**

```python
# The modern way (LCEL)
rag_chain = (
    {
        "context": retriever | format_docs,
        "question": RunnablePassthrough()
    }
    | prompt
    | llm
    | StrOutputParser()
)
```

**Flow:**

```
User Query
    ↓
Retriever.invoke(query)
  → Semantic search in ChromaDB
  → Top-K chunks (default: 5)
    ↓
Format documents into context string
    ↓
ChatPromptTemplate
  → System: "You are an AI recruiter..."
  → Context: Retrieved resume chunks
  → Question: User query
    ↓
ChatOpenAI (gpt-4o-mini, temp=0.3)
    ↓
StrOutputParser
    ↓
Answer + Source Citations
```

**Code:** `rag_langchain.py` → `query_with_retrieval_qa()`

---

#### **Conversational RAG (with History)**

```python
rag_chain = (
    {
        "context": retriever | format_docs,
        "question": RunnablePassthrough(),
        "chat_history": lambda x: formatted_history
    }
    | conversational_prompt
    | llm
    | StrOutputParser()
)
```

**Code:** `rag_langchain.py` → `query_with_conversational_chain()`

**Features:**

- Maintains conversation context
- References previous Q&A pairs
- Better for follow-up questions

```
User Query + Chat History
    ↓
Conversation Memory (ConversationBufferMemory)
    ↓
Context-Aware Retrieval
    ↓
Top-K Relevant Chunks + Previous Context
    ↓
Conversational Prompt
    ↓
ChatOpenAI
    ↓
Answer + Updated Memory
```

**Code:** `rag_langchain.py` → `query_with_conversational_chain()`

**Features:**

- Maintains conversation context
- Understands follow-up questions
- References previous answers

---

## Data Flow

### **1. Resume Upload & Parsing**

```python
POST /api/jobs/{job_id}/resumes
    ↓
FileStorageService.save_file()  # Local or S3
    ↓
BackgroundTask: parse_resume_background()
    ↓
TextExtractionService.extract_text_from_bytes()
    ↓
ResumeParserService.parse_resume()  # OpenAI
    ↓
Save to PostgreSQL (resume_data table)
    ↓
LangChainRAGService.add_documents_to_vectorstore()
    ↓
ChromaDB (with OpenAI embeddings)
```

---

### **2. Resume Scoring**

```python
POST /api/resumes/{resume_id}/score
    ↓
BackgroundTask: score_resume_background()
    ↓
ScoringService.score_resume()
    ├── Skills Match (50%)
    ├── Experience Level (25%)
    └── Semantic Similarity (25%) [OpenAI embeddings]
    ↓
Update PostgreSQL (resume.score, resume.rank)
```

---

### **3. RAG Query**

```python
POST /api/jobs/{job_id}/query
    ↓
LangChainRAGService.query_with_retrieval_qa()
    ↓
Chroma.as_retriever(search_kwargs={k: 5, filter: {job_id}})
    ↓
RetrievalQA.invoke(query)
    ├── Retrieve: Top 5 chunks
    ├── Prompt: Custom template
    └── Generate: ChatOpenAI
    ↓
Return: {answer, sources, chain_type}
```

---

## Database Schema

### **PostgreSQL Tables**

1. **users** - User accounts
2. **jobs** - Job postings
3. **resumes** - Resume files metadata
4. **resume_data** - Parsed structured data (JSONB)
5. **resume_embeddings** - ChromaDB reference (optional tracking)

### **ChromaDB Collection**

**Collection Name:** `resume_embeddings`

**Document Structure:**

```python
{
    "id": "resume_uuid_chunk_0",
    "document": "text chunk content...",
    "metadata": {
        "resume_id": "uuid",
        "candidate_name": "John Doe",
        "job_id": "uuid",
        "chunk_index": 0,
        "total_chunks": 15
    },
    "embedding": [0.123, -0.456, ...]  # 1536 dimensions
}
```

---

## LangChain Chains Configuration

### **RetrievalQA Chain**

```python
RetrievalQA.from_chain_type(
    llm=ChatOpenAI(model="gpt-4o-mini", temperature=0.3),
    chain_type="stuff",  # All docs in prompt
    retriever=vectorstore.as_retriever(
        search_type="similarity",
        search_kwargs={"k": 5, "filter": {"job_id": "..."}}
    ),
    return_source_documents=True,
    chain_type_kwargs={"prompt": custom_prompt}
)
```

**Pros:**

- Simple, fast
- Good for independent queries
- Direct answers

**Cons:**

- No conversation memory
- Each query is isolated

---

### **ConversationalRetrievalChain**

```python
ConversationalRetrievalChain.from_llm(
    llm=ChatOpenAI(model="gpt-4o-mini", temperature=0.3),
    retriever=vectorstore.as_retriever(...),
    memory=ConversationBufferMemory(
        memory_key="chat_history",
        return_messages=True
    ),
    return_source_documents=True
)
```

**Pros:**

- Maintains context
- Understands follow-ups
- Natural conversation flow

**Cons:**

- Slightly slower
- More complex
- Memory management needed

---

## Custom Prompt Template

```python
"""You are an expert AI recruiter assistant. Use the following resume excerpts to answer the recruiter's question.

Context from resumes:
{context}

Question: {question}

Instructions:
- Answer based ONLY on the provided resume excerpts
- Be specific and cite candidate names when mentioned
- If information isn't in the excerpts, clearly state that
- Provide actionable insights for the recruiter
- Keep your answer concise but informative

Answer:"""
```

**Why Custom Prompt:**

- Domain-specific (recruiting)
- Sets clear boundaries (only use provided context)
- Encourages citations
- Professional tone

---

## Performance Optimization

### **Chunking Strategy**

- **Chunk Size:** 1000 characters
- **Overlap:** 100 characters
- **Rationale:**
  - 1000 chars ≈ 250 tokens (fits well in context)
  - 100 char overlap prevents information loss at boundaries

### **Retrieval Settings**

- **Top K:** 5 (default)
- **Search Type:** Similarity (cosine)
- **Filter:** By job_id for focused results

### **LLM Settings**

- **Model:** gpt-4o-mini (fast + cost-effective)
- **Temperature:** 0.3 (factual but not rigid)
- **Max Tokens:** 500 (concise answers)

---

## Error Handling

1. **Parsing Failure:** Resume marked as "failed", embeddings not created
2. **Embedding Failure:** Logged but doesn't block parsing
3. **Query Failure:** Returns error message, preserves user experience
4. **Vector Store Issues:** Falls back gracefully

---

## Security Considerations

1. **Authentication:** All endpoints require JWT
2. **Authorization:** Job-owner checks on all operations
3. **Input Validation:** Pydantic schemas on all inputs
4. **File Upload:** Size limits, type validation
5. **API Keys:** Stored in environment variables

---

## Scalability Considerations

### **Current Setup (MVP)**

- Single-server deployment
- Persistent ChromaDB on disk
- Background tasks in-process

### **Production Scaling Options**

1. **Vector Store:** Migrate to managed Chroma Cloud or Pinecone
2. **Background Jobs:** Use Celery + Redis
3. **LLM Caching:** Add Redis cache for frequent queries
4. **Load Balancing:** Multiple API instances
5. **Database:** Read replicas for PostgreSQL

---

## Monitoring & Observability

**Key Metrics:**

- Parsing success rate
- Average query response time
- Token usage per query
- Vector store size
- API error rates

**Logging:**

- All LangChain operations logged
- Query patterns tracked
- Error traces captured

---

## Future Enhancements

1. **Advanced RAG:**
   - Hypothetical document embeddings
   - Multi-query retrieval
   - Reranking with cross-encoders

2. **LangChain Features:**
   - Agents for complex workflows
   - Tools for web search integration
   - Custom retrievers

3. **Evaluation:**
   - RAG metrics (faithfulness, relevance)
   - A/B testing different prompts
   - User feedback loops

---

**References:**

- LangChain Docs: <https://python.langchain.com>
- ChromaDB Docs: <https://docs.trychroma.com>
- OpenAI API: <https://platform.openai.com/docs>
