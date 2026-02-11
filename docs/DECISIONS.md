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
- Excellent JSON support (for resume metadata)
- pgvector extension available (if needed for embeddings)

---

#### 3. **ORM: SQLAlchemy 2.0**

**Chosen:** SQLAlchemy with async support  
**Alternatives Considered:** Tortoise ORM, raw SQL  
**Rationale:**

- Industry standard
- Async/await support in 2.0
- Better migration tools (Alembic)
- Type safety with Python 3.11

---

#### 4. **Vector Store: FAISS**

**Chosen:** FAISS (Facebook AI Similarity Search)  
**Alternatives Considered:** Chroma, Pinecone, Weaviate  
**Rationale:**

- Open source (no vendor lock-in)
- Runs locally (no external API costs)
- Extremely fast for similarity search
- Easy to persist to disk
- Production-proven

**Trade-off:** Less feature-rich than managed solutions, but perfect for MVP

---

#### 5. **LLM: OpenAI API**

**Chosen:** OpenAI GPT-4 via API  
**Alternatives Considered:** Open-source models (Llama, Mistral)  
**Rationale:**

- Best quality for structured extraction
- Reliable API
- Function calling support
- Easy to switch to Anthropic/other later

**Cost Consideration:** Will implement token counting and rate limiting

---

#### 6. **Frontend: React + Vite**

**Chosen:** React with Vite  
**Alternatives Considered:** Next.js, Vue, Svelte  
**Rationale:**

- React is industry standard
- Vite is faster than Create React App
- Better developer experience
- Easy component reusability

---

#### 7. **Authentication: JWT**

**Chosen:** JWT with HTTP-only cookies  
**Alternatives Considered:** Session-based, OAuth  
**Rationale:**

- Stateless (scales better)
- Standard in modern APIs
- Works well with FastAPI
- Simple to implement

**Security:** Will use short expiry + refresh tokens

---

#### 8. **File Storage: AWS S3**

**Chosen:** S3 for resume files  
**Alternatives Considered:** Local storage, Google Cloud Storage  
**Rationale:**

- Industry standard
- Unlimited scalability
- Cost-effective
- Easy CDN integration
- Will use local storage in development

---

#### 9. **Deployment: Docker + AWS EC2**

**Chosen:** Dockerized app on EC2  
**Alternatives Considered:** Kubernetes, Heroku, Railway  
**Rationale:**

- Full control over environment
- Cost-effective for MVP
- Docker ensures consistency
- Easy to migrate to ECS/EKS later

---

## Future Decisions Pending

- [ ] Caching strategy (Redis?)
- [ ] Background job processing (Celery?)
- [ ] Monitoring/observability tools
- [ ] CI/CD pipeline

---

## Lessons Learned

*To be updated as project progresses*

---

## References

- FastAPI: <https://fastapi.tiangolo.com>
- LangChain: <https://langchain.com>
- SQLAlchemy 2.0: <https://docs.sqlalchemy.org>
