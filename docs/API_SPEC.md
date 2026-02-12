# SmartHire - API Specification

**Base URL:** `http://localhost:8000`  
**API Version:** 1.0.0

---

## Authentication

All endpoints except `/api/auth/signup` and `/api/auth/login` require authentication.

**Authentication Method:** Bearer Token (JWT)

**Header Format:**

```
Authorization: Bearer <access_token>
```

---

## Endpoints

### **Authentication**

#### **POST /api/auth/signup**

Create a new user account.

**Request Body:**

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
  "is_superuser": false,
  "created_at": "2026-02-11T10:00:00",
  "updated_at": "2026-02-11T10:00:00"
}
```

---

#### **POST /api/auth/login**

Login with email and password.

**Request Body:**

```json
{
  "email": "user@example.com",
  "password": "password123"
}
```

**Response:** `200 OK`

```json
{
  "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
  "token_type": "bearer"
}
```

---

#### **GET /api/auth/me**

Get current user information.

**Headers:** `Authorization: Bearer <token>`

**Response:** `200 OK`

```json
{
  "id": "uuid",
  "email": "user@example.com",
  "full_name": "John Doe",
  "company_name": "Acme Corp",
  "is_active": true,
  "is_superuser": false,
  "created_at": "2026-02-11T10:00:00",
  "updated_at": "2026-02-11T10:00:00"
}
```

---

### **Jobs**

#### **POST /api/jobs**

Create a new job posting.

**Headers:** `Authorization: Bearer <token>`

**Request Body:**

```json
{
  "title": "Senior Backend Engineer",
  "description": "Full job description here...",
  "requirements": "5+ years Python, FastAPI, PostgreSQL",
  "location": "San Francisco, CA",
  "employment_type": "Full-time",
  "experience_level": "Senior",
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
  "description": "Full job description here...",
  "requirements": "5+ years Python, FastAPI, PostgreSQL",
  "location": "San Francisco, CA",
  "employment_type": "Full-time",
  "experience_level": "Senior",
  "salary_range": "$150k - $200k",
  "status": "open",
  "created_at": "2026-02-11T10:00:00",
  "updated_at": "2026-02-11T10:00:00"
}
```

---

#### **GET /api/jobs**

List all jobs for current user.

**Headers:** `Authorization: Bearer <token>`

**Query Parameters:**

- `status_filter` (optional): Filter by status (open, closed, draft)
- `skip` (optional): Pagination offset (default: 0)
- `limit` (optional): Number of results (default: 100, max: 100)

**Response:** `200 OK`

```json
[
  {
    "id": "uuid",
    "title": "Senior Backend Engineer",
    "location": "San Francisco, CA",
    "employment_type": "Full-time",
    "status": "open",
    "created_at": "2026-02-11T10:00:00"
  }
]
```

---

#### **GET /api/jobs/{job_id}**

Get a specific job by ID.

**Headers:** `Authorization: Bearer <token>`

**Response:** `200 OK`

```json
{
  "id": "uuid",
  "user_id": "uuid",
  "title": "Senior Backend Engineer",
  "description": "...",
  "requirements": "...",
  "location": "San Francisco, CA",
  "employment_type": "Full-time",
  "experience_level": "Senior",
  "salary_range": "$150k - $200k",
  "status": "open",
  "created_at": "2026-02-11T10:00:00",
  "updated_at": "2026-02-11T10:00:00"
}
```

---

#### **PUT /api/jobs/{job_id}**

Update a job posting.

**Headers:** `Authorization: Bearer <token>`

**Request Body:** (all fields optional)

```json
{
  "title": "Updated Title",
  "status": "closed"
}
```

**Response:** `200 OK`

```json
{
  "id": "uuid",
  "user_id": "uuid",
  "title": "Updated Title",
  "status": "closed",
  ...
}
```

---

#### **DELETE /api/jobs/{job_id}**

Delete a job posting.

**Headers:** `Authorization: Bearer <token>`

**Response:** `204 No Content`

**Note:** This will cascade delete all associated resumes.

---

#### **GET /api/jobs/{job_id}/stats**

Get statistics for a job.

**Headers:** `Authorization: Bearer <token>`

**Response:** `200 OK`

```json
{
  "job_id": "uuid",
  "job_title": "Senior Backend Engineer",
  "total_resumes": 15,
  "parsed_resumes": 12,
  "pending_resumes": 3,
  "average_score": 78.5
}
```

---

## Error Responses

### **400 Bad Request**

```json
{
  "detail": "Invalid input data"
}
```

### **401 Unauthorized**

```json
{
  "detail": "Invalid authentication credentials"
}
```

### **403 Forbidden**

```json
{
  "detail": "Not authorized to access this resource"
}
```

### **404 Not Found**

```json
{
  "detail": "Resource not found"
}
```

### **422 Validation Error**

```json
{
  "detail": [
    {
      "loc": ["body", "email"],
      "msg": "invalid email format",
      "type": "value_error"
    }
  ]
}
```

---

## Status Codes

- `200` - OK
- `201` - Created
- `204` - No Content
- `400` - Bad Request
- `401` - Unauthorized
- `403` - Forbidden
- `404` - Not Found
- `422` - Validation Error
- `500` - Internal Server Error

---

## Rate Limiting

Not implemented yet. Will be added in production.

---

## Coming Soon

- **Resume Management:**
  - `POST /api/jobs/{job_id}/resumes` - Upload resume
  - `GET /api/jobs/{job_id}/resumes` - List resumes
  - `GET /api/resumes/{resume_id}` - Get resume details
  
- **AI Features:**
  - `POST /api/resumes/{resume_id}/parse` - Parse resume
  - `POST /api/jobs/{job_id}/score` - Score all resumes
  - `POST /api/jobs/{job_id}/query` - RAG query

---

**Last Updated:** 2026-02-11
