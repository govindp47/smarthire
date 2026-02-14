# SmartHire - Technical Decisions Log

This document tracks all major technical decisions, their rationale, and alternatives considered.

---

## Decision Log

### 2026-02-11: Project Foundation

#### 1. **Backend Framework: FastAPI**

**Chosen:** FastAPI  
**Alternatives Considered:** Django REST, Flask  
**Rationale:**

- Native async support (better for AI/LLM calls)
- Automatic API documentation (Swagger/OpenAPI)
- Type hints + Pydantic validation (fewer bugs)
- Fast development speed
- Modern Python features

---

#### 2. **Database: PostgreSQL**

**Chosen:** PostgreSQL 15  
**Alternatives Considered:** MySQL, MongoDB  
**Rationale:**

- Industry standard for production
- ACID compliance
- Better for relational data (users, jobs, resumes)
- Excellent JSONB support (for resume metadata)
- Mature ecosystem

---

#### 3. **ORM: SQLAlchemy 2.0**

**Chosen:** SQLAlchemy with async support  
**Alternatives Considered:** Tortoise ORM, raw SQL  
**Rationale:**

- Industry standard
- Async/await support in 2.0
- Better migration tools (Alembic)
- Type safety with Python 3.11
- Comprehensive documentation

---

#### 4. **Vector Store: ChromaDB**

**Chosen:** ChromaDB  
**Alternatives Considered:** FAISS, Pinecone, Weaviate  
**Rationale:**

- Open source (no vendor lock-in)
- Native LangChain integration
- Persistent storage with SQLite backend
- Simple API for embeddings
- Active development and community

**Trade-off:** Less performant than FAISS at massive scale, but perfect for our use case (hundreds/thousands of resumes)

---

#### 5. **LLM Framework: LangChain 1.0+**

**Chosen:** LangChain with LCEL patterns  
**Alternatives Considered:** LlamaIndex, custom implementation  
**Rationale:**

- Industry standard for RAG applications
- Modern LCEL (no legacy chains)
- Excellent OpenAI integration
- Vector store abstractions
- Active community and updates

**Key Decision:** Use modern LCEL patterns, avoid deprecated chains

---

#### 6. **LLM: OpenAI GPT-4o-mini**

**Chosen:** OpenAI GPT-4o-mini via API  
**Alternatives Considered:** GPT-4, Claude, Open-source models (Llama)  
**Rationale:**

- Best quality/cost ratio for structured extraction
- Fast response times
- Reliable API
- JSON mode support
- Easy to switch providers later

**Cost Consideration:** Using mini model instead of GPT-4 reduces costs by ~10x while maintaining quality

---

#### 7. **Embeddings: OpenAI text-embedding-ada-002**

**Chosen:** text-embedding-ada-002  
**Alternatives Considered:** sentence-transformers, Cohere  
**Rationale:**

- High quality embeddings
- 1536 dimensions (good balance)
- Cost-effective ($0.0001/1K tokens)
- Maintained by OpenAI
- Works well with ChromaDB

---

#### 8. **Frontend: React + Vite**

**Chosen:** React 18 with Vite  
**Alternatives Considered:** Next.js, Vue, Svelte  
**Rationale:**

- React is industry standard
- Vite is much faster than Create React App
- Better developer experience (HMR)
- Easy component reusability
- Large ecosystem

---

#### 9. **Styling: Tailwind CSS**

**Chosen:** Tailwind CSS  
**Alternatives Considered:** Material-UI, Ant Design, styled-components  
**Rationale:**

- Utility-first approach (faster development)
- Smaller bundle size
- Highly customizable
- Modern design patterns
- Great documentation

---

#### 10. **State Management: React Context + TanStack Query**

**Chosen:** Context API + TanStack Query (React Query)  
**Alternatives Considered:** Redux, Zustand, Jotai  
**Rationale:**

- Context API sufficient for auth state
- React Query handles server state perfectly
- Built-in caching and optimistic updates
- No need for Redux complexity
- Less boilerplate

---

#### 11. **Authentication: JWT**

**Chosen:** JWT tokens in localStorage  
**Alternatives Considered:** HTTP-only cookies, sessions  
**Rationale:**

- Stateless (scales better)
- Standard in modern SPAs
- Works well with FastAPI
- Simple to implement
- Easy to debug

**Security:** Short expiry times, stored in localStorage (acceptable for portfolio project)

---

#### 12. **File Storage: Local + S3-ready**

**Chosen:** Local filesystem with S3 abstraction  
**Alternatives Considered:** Direct S3, Google Cloud Storage  
**Rationale:**

- Easy local development
- Abstraction layer for future S3 migration
- Cost-effective for development
- Simple to test

**Production Plan:** Switch to S3 with environment variable

---

#### 13. **Deployment Architecture: Docker + AWS**

**Chosen:** Dockerized app on EC2 with RDS  
**Alternatives Considered:** Kubernetes, Heroku, Vercel  
**Rationale:**

- Full control over environment
- Cost-effective for portfolio
- Docker ensures consistency
- Easy to migrate to ECS/EKS later
- Industry-standard approach

---

### 2026-02-13: AI Implementation Decisions

#### 14. **Resume Parsing: LLM-based**

**Chosen:** GPT-4o-mini with structured prompts  
**Alternatives Considered:** Regex patterns, spaCy NER, traditional parsers  
**Rationale:**

- More accurate than regex
- Handles varied resume formats
- Extracts semantic information
- No training required
- Easy to improve prompts

**Trade-off:** API costs vs accuracy - worth it for quality

---

#### 15. **Scoring Algorithm: Multi-factor Weighted**

**Chosen:** Skills (50%) + Experience (25%) + Semantic (25%)  
**Alternatives Considered:** Pure ML model, simple keyword matching  
**Rationale:**

- Transparent and explainable
- Balances multiple factors
- No training data required
- Easy to tune weights
- Good results in testing

---

#### 16. **Background Processing: FastAPI BackgroundTasks**

**Chosen:** Built-in BackgroundTasks  
**Alternatives Considered:** Celery, RQ, ARQ  
**Rationale:**

- Simple for our use case
- No additional infrastructure (Redis)
- Good enough for hundreds of resumes
- Easy to understand

**Future:** May need Celery for production scale

---

#### 17. **Singleton Pattern for LLM Instances**

**Chosen:** LRU cache for OpenAI clients  
**Alternatives Considered:** Module-level globals, dependency injection  
**Rationale:**

- Avoids re-initialization overhead
- Better connection pooling
- Recommended by LangChain/OpenAI
- Simple implementation

---

## Lessons Learned

### What Went Well

1. **FastAPI's async support** - Made AI calls much cleaner
2. **LangChain LCEL** - Modern patterns are more composable than legacy chains
3. **ChromaDB integration** - Worked seamlessly with LangChain
4. **React Query** - Eliminated most state management complexity
5. **Tailwind CSS** - Rapid UI development

### What We'd Change

1. **Earlier LangChain pattern research** - Spent time with deprecated chains before LCEL
2. **Batch processing from start** - Should have designed for batch from beginning
3. **More comprehensive error handling** - Some edge cases discovered late
4. **Testing strategy** - Should have written tests alongside features

### Key Insights

- AI features need careful prompt engineering
- Vector search quality depends heavily on chunking strategy
- Background tasks are essential for good UX with slow AI operations
- Singleton patterns critical for LLM performance

---

## Future Considerations

### Phase 4+

- [ ] Redis caching for API responses
- [ ] Celery for production-grade background jobs
- [ ] Rate limiting implementation
- [ ] Monitoring/observability (Sentry, DataDog)
- [ ] CI/CD pipeline (GitHub Actions)
- [ ] Automated testing suite
- [ ] Performance optimization (database indexes, query optimization)
- [ ] Multi-tenancy features
- [ ] Advanced filtering and search
- [ ] Email notifications

---

## References

- **FastAPI**: <https://fastapi.tiangolo.com>
- **LangChain**: <https://python.langchain.com>
- **ChromaDB**: <https://www.trychroma.com>
- **SQLAlchemy 2.0**: <https://docs.sqlalchemy.org>
- **React Query**: <https://tanstack.com/query>
- **Tailwind CSS**: <https://tailwindcss.com>

---

**Last Updated:** 2026-02-15
