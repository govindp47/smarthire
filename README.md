# 🎯 SmartHire - AI-Powered Resume Screening SaaS

**An intelligent ATS alternative that uses AI to rank candidates, extract structured data, and answer natural language queries about resumes.**

---

## 🚀 Features

- **Job Management** - Create and manage job postings
- **Resume Upload** - Bulk resume processing (PDF/DOCX)
- **AI Parsing** - Structured data extraction (skills, experience, education)
- **Smart Scoring** - Semantic ranking based on job requirements
- **Natural Language Queries** - Ask questions like "Who has 5+ years in Python and AWS?"
- **RAG-Powered Search** - Context-aware resume retrieval
- **Multi-tenant** - Separate workspaces for recruiters

---

## 🛠️ Tech Stack

### Backend

- **FastAPI** - Modern Python web framework
- **PostgreSQL** - Primary database
- **SQLAlchemy** - ORM with async support
- **Alembic** - Database migrations

### AI/ML

- **LangChain** - LLM orchestration framework
- **OpenAI GPT-4** - Language model
- **FAISS** - Vector similarity search
- **Sentence Transformers** - Embeddings

### Frontend

- **React** - UI framework
- **Vite** - Build tool
- **Tailwind CSS** - Styling (to be added)

### Infrastructure

- **Docker** - Containerization
- **AWS S3** - Resume storage
- **AWS RDS** - Managed PostgreSQL
- **AWS EC2** - Application hosting

---

## 📁 Project Structure

```
smarthire/
├── backend/          # FastAPI application
│   ├── app/
│   │   ├── api/      # API routes
│   │   ├── models/   # Database models
│   │   ├── schemas/  # Pydantic schemas
│   │   ├── services/ # Business logic
│   │   └── core/     # Config, security
│   └── tests/        # Unit tests
├── frontend/         # React application
│   └── src/
├── docs/             # Project documentation
└── docker-compose.yml
```

---

## 🏃 Quick Start

### Prerequisites

- Python 3.11+
- PostgreSQL 15+
- Node.js 18+
- Docker (optional)

### Backend Setup

```bash
cd backend
python3.11 -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
pip install -r requirements.txt

# Setup environment
cp .env.example .env
# Edit .env with your credentials

# Run migrations
alembic upgrade head

# Start server
uvicorn app.main:app --reload
```

API will be available at: <http://localhost:8000>  
Docs: <http://localhost:8000/docs>

### Frontend Setup

```bash
cd frontend
npm install
npm run dev
```

Frontend will be available at: <http://localhost:5173>

---

## 📚 Documentation

- [Project State](docs/PROJECT_STATE.md) - Current progress
- [Architecture](docs/ARCHITECTURE.md) - System design
- [API Specification](docs/API_SPEC.md) - Endpoint details
- [Database Schema](docs/DATABASE_SCHEMA.md) - Data models
- [Decisions Log](docs/DECISIONS.md) - Technical choices

---

## 🗄️ Database Schema

See [DATABASE_SCHEMA.md](docs/DATABASE_SCHEMA.md) for complete schema.

**Core Tables:**

- `users` - Recruiter accounts
- `jobs` - Job postings
- `resumes` - Candidate resumes
- `resume_data` - Parsed structured data
- `embeddings` - Vector representations

---

## 🔐 Environment Variables

See `.env.example` for all required variables.

**Critical:**

- `DATABASE_URL` - PostgreSQL connection
- `SECRET_KEY` - JWT signing key
- `OPENAI_API_KEY` - OpenAI API access
- `AWS_*` - S3 credentials

---

## 🧪 Testing

```bash
cd backend
pytest
pytest --cov=app tests/  # With coverage
```

---

## 🐳 Docker Deployment

```bash
docker-compose up --build
```

---

## 📈 Roadmap

- [x] Phase 0: Foundation
- [ ] Phase 1: Core Backend (Auth, Jobs, Resumes)
- [ ] Phase 2: AI Features (Parsing, RAG, Scoring)
- [ ] Phase 3: Frontend UI
- [ ] Phase 4: AWS Deployment

---

## 🤝 Contributing

This is a learning/portfolio project. Feedback and suggestions welcome!

---

## 📄 License

MIT License - See LICENSE file

---

## 👤 Author

Built as a demonstration project for AI Engineer role applications.

---

## 🙏 Acknowledgments

- FastAPI community
- LangChain documentation
- OpenAI API

---

**Status:** 🚧 In Development  
**Last Updated:** February 2026
