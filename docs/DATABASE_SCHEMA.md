# SmartHire - Database Schema

**Database:** PostgreSQL 15  
**ORM:** SQLAlchemy 2.0 (async)  
**Migrations:** Alembic

---

## Entity Relationship Diagram

```
┌─────────────┐
│    users    │
└──────┬──────┘
       │ 1
       │
       │ N
┌──────┴──────┐
│    jobs     │
└──────┬──────┘
       │ 1
       │
       │ N
┌──────┴──────────┐
│    resumes      │
└──────┬──────────┘
       │ 1
       ├─────────────┐
       │ 1           │ 1
       │             │
       │ 1           │ 1
┌──────┴────────┐ ┌─┴──────────────────┐
│ resume_data   │ │ resume_embeddings  │
└───────────────┘ └────────────────────┘
```

---

## Table Schemas

### **1. users**

Stores recruiter/company accounts.

| Column | Type | Constraints | Description |
|--------|------|-------------|-------------|
| id | UUID | PK | Unique user ID |
| email | VARCHAR(255) | UNIQUE, NOT NULL | Login email |
| hashed_password | VARCHAR(255) | NOT NULL | Bcrypt hash |
| full_name | VARCHAR(255) | NOT NULL | Display name |
| company_name | VARCHAR(255) | NULLABLE | Organization |
| is_active | BOOLEAN | DEFAULT TRUE | Account status |
| is_superuser | BOOLEAN | DEFAULT FALSE | Admin flag |
| created_at | TIMESTAMP | NOT NULL | Registration time |
| updated_at | TIMESTAMP | NOT NULL | Last modification |

**Indexes:**

- `idx_users_email` on `email`

---

### **2. jobs**

Job postings created by recruiters.

| Column | Type | Constraints | Description |
|--------|------|-------------|-------------|
| id | UUID | PK | Unique job ID |
| user_id | UUID | FK(users.id), NOT NULL | Job creator |
| title | VARCHAR(255) | NOT NULL | Job title |
| description | TEXT | NOT NULL | Full job description |
| requirements | TEXT | NULLABLE | Skills/qualifications |
| location | VARCHAR(255) | NULLABLE | Job location |
| employment_type | VARCHAR(50) | NULLABLE | Full-time, Contract, etc |
| experience_level | VARCHAR(50) | NULLABLE | Junior, Mid, Senior |
| salary_range | VARCHAR(100) | NULLABLE | Compensation info |
| status | VARCHAR(50) | DEFAULT 'open' | open, closed, draft |
| created_at | TIMESTAMP | NOT NULL | Creation time |
| updated_at | TIMESTAMP | NOT NULL | Last modification |

**Indexes:**

- `idx_jobs_user_id` on `user_id`
- `idx_jobs_status` on `status`

**Constraints:**

- `CHECK (status IN ('open', 'closed', 'draft'))`

---

### **3. resumes**

Uploaded candidate resumes linked to jobs.

| Column | Type | Constraints | Description |
|--------|------|-------------|-------------|
| id | UUID | PK | Unique resume ID |
| job_id | UUID | FK(jobs.id), NOT NULL | Associated job |
| candidate_name | VARCHAR(255) | NULLABLE | Extracted name |
| candidate_email | VARCHAR(255) | NULLABLE | Contact email |
| file_name | VARCHAR(255) | NOT NULL | Original filename |
| file_path | TEXT | NOT NULL | S3 path or local path |
| file_size | INTEGER | NOT NULL | Size in bytes |
| file_type | VARCHAR(10) | NOT NULL | pdf, docx |
| upload_status | VARCHAR(50) | DEFAULT 'uploaded' | Processing status |
| parsing_status | VARCHAR(50) | DEFAULT 'pending' | pending, completed, failed |
| score | FLOAT | NULLABLE | AI-calculated score (0-100) |
| rank | INTEGER | NULLABLE | Position in ranking |
| created_at | TIMESTAMP | NOT NULL | Upload time |
| updated_at | TIMESTAMP | NOT NULL | Last modification |

**Indexes:**

- `idx_resumes_job_id` on `job_id`
- `idx_resumes_score` on `score` DESC
- `idx_resumes_parsing_status` on `parsing_status`

**Constraints:**

- `CHECK (file_type IN ('pdf', 'docx'))`
- `CHECK (parsing_status IN ('pending', 'processing', 'completed', 'failed'))`
- `CHECK (score >= 0 AND score <= 100)`

---

### **4. resume_data**

Structured data extracted from resumes by AI.

| Column | Type | Constraints | Description |
|--------|------|-------------|-------------|
| id | UUID | PK | Unique record ID |
| resume_id | UUID | FK(resumes.id), UNIQUE, NOT NULL | One-to-one relationship |
| raw_text | TEXT | NULLABLE | Extracted text |
| skills | JSONB | DEFAULT '[]' | Array of skills |
| experience | JSONB | DEFAULT '[]' | Work history objects |
| education | JSONB | DEFAULT '[]' | Education objects |
| certifications | JSONB | DEFAULT '[]' | Certifications |
| languages | JSONB | DEFAULT '[]' | Languages spoken |
| total_experience_years | FLOAT | NULLABLE | Calculated experience |
| summary | TEXT | NULLABLE | AI-generated summary |
| metadata | JSONB | DEFAULT '{}' | Additional extracted data |
| created_at | TIMESTAMP | NOT NULL | Parse time |
| updated_at | TIMESTAMP | NOT NULL | Last modification |

**Indexes:**

- `idx_resume_data_resume_id` on `resume_id` (unique)
- `idx_resume_data_skills` GIN index on `skills` (for fast JSONB queries)
- `idx_resume_data_experience_years` on `total_experience_years`

**JSONB Structure Examples:**

**skills:**

```json
["Python", "FastAPI", "PostgreSQL", "Docker", "AWS"]
```

**experience:**

```json
[
  {
    "title": "Senior Backend Engineer",
    "company": "Tech Corp",
    "location": "San Francisco, CA",
    "start_date": "2020-01",
    "end_date": "2023-12",
    "duration_months": 48,
    "description": "Led team of 5 engineers..."
  }
]
```

**education:**

```json
[
  {
    "degree": "Bachelor of Science",
    "field": "Computer Science",
    "institution": "Stanford University",
    "graduation_year": 2019,
    "gpa": 3.8
  }
]
```

---

### **5. resume_embeddings**

Vector embeddings for RAG/semantic search.

| Column | Type | Constraints | Description |
|--------|------|-------------|-------------|
| id | UUID | PK | Unique embedding ID |
| resume_id | UUID | FK(resumes.id), NOT NULL | Parent resume |
| chunk_text | TEXT | NOT NULL | Text chunk (for context) |
| chunk_index | INTEGER | NOT NULL | Position in document |
| embedding_vector | VECTOR(1536) | NOT NULL | OpenAI embedding (if using pgvector) OR store as BYTEA |
| metadata | JSONB | DEFAULT '{}' | Chunk metadata |
| created_at | TIMESTAMP | NOT NULL | Embedding time |

**Note:** If not using pgvector extension, we store embeddings in ChromaDB externally and only keep reference here.

**Simplified version (without pgvector):**

| Column | Type | Constraints | Description |
|--------|------|-------------|-------------|
| id | UUID | PK | Unique embedding ID |
| resume_id | UUID | FK(resumes.id), NOT NULL | Parent resume |
| chroma_id | VARCHAR(255) | UNIQUE, NOT NULL | ChromaDB document ID |
| chunk_text | TEXT | NOT NULL | Original text chunk |
| chunk_index | INTEGER | NOT NULL | Chunk position |
| metadata | JSONB | DEFAULT '{}' | Additional info |
| created_at | TIMESTAMP | NOT NULL | Creation time |

**Indexes:**

- `idx_resume_embeddings_resume_id` on `resume_id`
- `idx_resume_embeddings_chroma_id` on `chroma_id` (unique)

---

## Relationships Summary

```
users (1) ──→ (N) jobs
jobs (1) ──→ (N) resumes
resumes (1) ──→ (1) resume_data
resumes (1) ──→ (N) resume_embeddings
```

---

## Data Flow

1. **User signs up** → Insert into `users`
2. **User creates job** → Insert into `jobs`
3. **Upload resume** → Insert into `resumes` (status: uploaded, parsing: pending)
4. **AI parses resume** → Insert into `resume_data` + Update `resumes.parsing_status`
5. **Generate embeddings** → Insert chunks into `resume_embeddings` + Store vectors in ChromaDB
6. **Calculate score** → Update `resumes.score` and `resumes.rank`
7. **RAG query** → Query ChromaDB → Retrieve chunks from `resume_embeddings` → Generate answer

---

## Future Enhancements (Not in MVP)

- **resume_screening_history** - Track all queries made
- **resume_notes** - Recruiter notes on candidates
- **resume_tags** - Custom categorization
- **audit_log** - Track all actions

---

## Migration Strategy

We'll use **Alembic** for all schema changes:

```bash
# Create migration
alembic revision --autogenerate -m "Create initial tables"

# Apply migration
alembic upgrade head

# Rollback
alembic downgrade -1
```

---

## Sample Queries

**Get all resumes for a job, ranked by score:**

```sql
SELECT r.*, rd.skills, rd.total_experience_years
FROM resumes r
LEFT JOIN resume_data rd ON r.id = rd.resume_id
WHERE r.job_id = '...'
ORDER BY r.score DESC NULLS LAST;
```

**Search resumes by skill (JSONB query):**

```sql
SELECT r.candidate_name, rd.skills
FROM resumes r
JOIN resume_data rd ON r.id = rd.resume_id
WHERE rd.skills @> '["Python"]'::jsonb;
```

**Get top candidates with 5+ years experience:**

```sql
SELECT r.*, rd.total_experience_years
FROM resumes r
JOIN resume_data rd ON r.id = rd.resume_id
WHERE rd.total_experience_years >= 5
ORDER BY r.score DESC
LIMIT 10;
```

---

## Performance Considerations

- **Indexes:** Created on all FK columns and frequently queried fields
- **JSONB:** GIN indexes for fast skill/experience queries
- **Partitioning:** Can partition `resumes` by `created_at` if scale grows
- **Caching:** Can add Redis for frequently accessed job listings
- **Vector Search:** ChromaDB handles embedding search separately (not in PostgreSQL)

---

**Last Updated:** 2026-02-11  
**Status:** Ready for implementation
