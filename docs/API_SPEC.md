# SmartHire - API Specification

**Base URL:** `http://localhost:8000`  
**API Version:** 1.0.0  
**Documentation:** `http://localhost:8000/docs` (Swagger UI)

---

## Authentication

All endpoints except `/api/auth/signup` and `/api/auth/login` require authentication.

**Authentication Method:** Bearer Token (JWT)

**Header Format:**

```
Authorization: Bearer <access_token>
```

---

## Endpoints Overview

### Authentication (`/api/auth`)

- `POST /signup` - Create account
- `POST /login` - Get JWT token
- `GET /me` - Get current user

### Jobs (`/api/jobs`)

- `POST /jobs` - Create job
- `GET /jobs` - List jobs
- `GET /jobs/{id}` - Get job details
- `PUT /jobs/{id}` - Update job
- `DELETE /jobs/{id}` - Delete job
- `GET /jobs/{id}/stats` - Get resume statistics
- `GET /jobs/{id}/leaderboard` - Get top candidates

### Resumes (`/api/jobs/{job_id}/resumes`)

- `POST /jobs/{job_id}/resumes` - Upload resume
- `GET /jobs/{job_id}/resumes` - List resumes for job
- `GET /resumes/{id}` - Get resume details
- `GET /resumes/{id}/download` - Download resume file
- `DELETE /resumes/{id}` - Delete resume

### Parsing (`/api`)

- `POST /resumes/{id}/parse` - Parse single resume
- `POST /jobs/{job_id}/parse-all` - Parse all pending resumes
- `GET /resumes/{id}/parsed-data` - Get parsed data

### Scoring (`/api`)

- `POST /resumes/{id}/score` - Score single resume
- `POST /jobs/{job_id}/score-all` - Score all resumes

### RAG Query (`/api`)

- `POST /jobs/{job_id}/query` - Query job's resumes
- `POST /query` - Query all resumes
- `GET /jobs/{job_id}/vector-stats` - Vector store stats
- `GET /vector-store/stats` - Global vector store stats

---

## Detailed Endpoints

### Authentication

#### POST /api/auth/signup

Create a new user account.

**Request:**

```json
{
  "email": "user@example.com",
  "password": "password123",
  "full_name": "John Doe",
  "company_name": "Acme Corp"
}
```

**Response:** `201 Created`

```json
{
  "id": "uuid",
  "email": "user@example.com",
  "full_name": "John Doe",
  "company_name": "Acme Corp",
  "is_active": true,
  "created_at": "2026-02-15T10:00:00"
}
```

#### POST /api/auth/login

Authenticate and get JWT token.

**Request:**

```json
{
  "email": "user@example.com",
  "password": "password123"
}
```

**Response:** `200 OK`

```json
{
  "access_token": "eyJ0eXAiOiJKV1QiLCJhbGc...",
  "token_type": "bearer"
}
```

#### GET /api/auth/me

Get current authenticated user.

**Headers:** `Authorization: Bearer <token>`

**Response:** `200 OK`

```json
{
  "id": "uuid",
  "email": "user@example.com",
  "full_name": "John Doe",
  "company_name": "Acme Corp"
}
```

---

### Jobs

#### POST /api/jobs

Create a new job posting.

**Request:**

```json
{
  "title": "Senior Backend Engineer",
  "description": "We are looking for...",
  "requirements": "5+ years Python, FastAPI...",
  "location": "San Francisco, CA",
  "employment_type": "full-time",
  "experience_level": "senior",
  "salary_range": "$150k - $200k",
  "status": "open"
}
```

**Response:** `201 Created`

```json
{
  "id": "uuid",
  "user_id": "uuid",
  "title": "Senior Backend Engineer",
  "status": "open",
  "created_at": "2026-02-15T10:00:00"
}
```

#### GET /api/jobs/{id}/stats

Get statistics for a job's resumes.

**Response:** `200 OK`

```json
{
  "total_resumes": 25,
  "parsed_resumes": 23,
  "pending_resumes": 2,
  "average_score": 78.5
}
```

#### GET /api/jobs/{id}/leaderboard

Get top-ranked candidates.

**Query Params:** `limit` (default: 10)

**Response:** `200 OK`

```json
[
  {
    "resume_id": "uuid",
    "candidate_name": "John Doe",
    "score": 92.5,
    "rank": 1,
    "file_name": "john_resume.pdf"
  }
]
```

---

### Resumes

#### POST /api/jobs/{job_id}/resumes

Upload a resume file.

**Content-Type:** `multipart/form-data`

**Form Data:**

- `file`: PDF or DOCX file (max 5MB)

**Response:** `201 Created`

```json
{
  "id": "uuid",
  "job_id": "uuid",
  "file_name": "resume.pdf",
  "file_size": 245678,
  "file_type": "pdf",
  "upload_status": "completed",
  "parsing_status": "pending",
  "created_at": "2026-02-15T10:00:00"
}
```

#### GET /api/resumes/{id}/parsed-data

Get parsed resume data (requires parsing_status='completed').

**Response:** `200 OK`

```json
{
  "id": "uuid",
  "candidate_name": "John Doe",
  "candidate_email": "john@example.com",
  "score": 85.3,
  "resume_data": {
    "skills": ["Python", "FastAPI", "PostgreSQL"],
    "experience": [
      {
        "title": "Senior Engineer",
        "company": "Tech Corp",
        "start_date": "2020-01",
        "end_date": "Present",
        "duration_months": 48
      }
    ],
    "education": [
      {
        "degree": "B.S. Computer Science",
        "institution": "MIT",
        "graduation_year": 2020
      }
    ],
    "total_experience_years": 5.2,
    "summary": "Experienced backend engineer..."
  }
}
```

---

### Parsing

#### POST /api/resumes/{id}/parse

Trigger parsing for a single resume (async).

**Response:** `200 OK`

```json
{
  "message": "Resume parsing started",
  "resume_id": "uuid",
  "status": "processing"
}
```

#### POST /api/jobs/{job_id}/parse-all

Parse all pending resumes for a job (async).

**Response:** `200 OK`

```json
{
  "message": "Parsing started for 15 resumes",
  "job_id": "uuid",
  "count": 15
}
```

---

### Scoring

#### POST /api/jobs/{job_id}/score-all

Score all parsed resumes and update rankings.

**Response:** `200 OK`

```json
{
  "message": "Scoring started for 15 resumes",
  "job_id": "uuid",
  "count": 15
}
```

---

### RAG Query

#### POST /api/jobs/{job_id}/query

Query resumes using natural language.

**Request:**

```json
{
  "query": "Who has 5+ years of Python experience?",
  "top_k": 5,
  "use_conversation": false,
  "chat_history": []
}
```

**Response:** `200 OK`

```json
{
  "answer": "Based on the resumes, John Doe has 7 years of Python...",
  "sources": [
    {
      "resume_id": "uuid",
      "candidate_name": "John Doe",
      "relevance_score": 0.92,
      "excerpt": "Senior Backend Engineer with 7 years..."
    }
  ],
  "query": "Who has 5+ years of Python experience?",
  "num_sources": 3
}
```

---

## Error Responses

All endpoints return consistent error format:

**400 Bad Request**

```json
{
  "detail": "Invalid input data"
}
```

**401 Unauthorized**

```json
{
  "detail": "Could not validate credentials"
}
```

**403 Forbidden**

```json
{
  "detail": "Not authorized to access this resource"
}
```

**404 Not Found**

```json
{
  "detail": "Resource not found"
}
```

**500 Internal Server Error**

```json
{
  "detail": "Internal server error"
}
```

---

## Rate Limiting

Currently not implemented. To be added in production.

---

## Versioning

API version is included in base URL. Current version: v1

Future versions will be available at: `/api/v2/...`

---

For interactive API documentation, visit: `http://localhost:8000/docs`
