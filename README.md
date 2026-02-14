# SmartHire - AI-Powered Resume Screening Platform

<div align="center">

![SmartHire](https://img.shields.io/badge/SmartHire-AI--Powered-blue)
![Python](https://img.shields.io/badge/Python-3.11+-green)
![FastAPI](https://img.shields.io/badge/FastAPI-0.109+-teal)
![React](https://img.shields.io/badge/React-18+-blue)
![License](https://img.shields.io/badge/License-MIT-yellow)

**Intelligent resume screening and candidate matching powered by AI**

[Features](#features) • [Tech Stack](#tech-stack) • [Getting Started](#getting-started) • [Documentation](#documentation)

</div>

---

## 🎯 Overview

SmartHire is a modern SaaS platform that revolutionizes the recruitment process using artificial intelligence. It automatically parses resumes, scores candidates against job requirements, and enables natural language queries over your candidate database using Retrieval Augmented Generation (RAG).

### Key Capabilities

- 🤖 **AI Resume Parsing** - Automatically extract skills, experience, and education from PDFs and DOCX files
- ⚡ **Smart Scoring** - Multi-factor algorithm scoring candidates based on skills (50%), experience (25%), and semantic similarity (25%)
- 🔍 **Semantic Search** - Find candidates using natural language queries powered by LangChain RAG
- 📊 **Intelligent Ranking** - Automatically rank candidates by match score
- 💬 **AI Chat Interface** - Ask questions about your candidate pool in plain English
- 🎨 **Modern UI** - Clean, responsive interface built with React and Tailwind CSS

---

## ✨ Features

### For Recruiters

- **Job Management**: Create and manage multiple job postings
- **Resume Upload**: Drag-and-drop interface supporting PDF and DOCX files
- **Automated Processing**: Batch parse and score hundreds of resumes in minutes
- **Smart Filtering**: Search and filter candidates by status, score, and more
- **AI-Powered Insights**: Ask questions like "Who has 5+ years of Python and AWS experience?"
- **Detailed Profiles**: View extracted skills, experience, education, and summaries

### Technical Features

- **RESTful API**: FastAPI backend with full OpenAPI documentation
- **Async Processing**: Background tasks for parsing and scoring
- **Scalable Storage**: Support for local filesystem and AWS S3
- **Vector Database**: ChromaDB for semantic search capabilities
- **Real-time Updates**: React Query for optimistic updates and caching
- **Secure Authentication**: JWT-based auth with password hashing

---

## 🛠 Tech Stack

### Backend

- **Framework**: FastAPI (Python 3.11+)
- **Database**: PostgreSQL 15 with SQLAlchemy (async)
- **AI/ML**:
  - OpenAI GPT-4o-mini for resume parsing and chat
  - LangChain 1.0+ with LCEL (modern patterns)
  - ChromaDB for vector storage
  - OpenAI embeddings (text-embedding-ada-002)
- **File Storage**: Local filesystem / AWS S3
- **Background Tasks**: FastAPI BackgroundTasks
- **Migrations**: Alembic

### Frontend

- **Framework**: React 18 with Vite
- **Styling**: Tailwind CSS
- **Routing**: React Router v6
- **State Management**: React Context + TanStack Query
- **HTTP Client**: Axios
- **Icons**: Lucide React

### DevOps (Ready)

- **Containerization**: Docker + Docker Compose
- **Deployment**: AWS (EC2, RDS, S3)
- **Environment**: Python venv, npm

---

## 🚀 Getting Started

### Prerequisites

- Python 3.11+
- Node.js 18+
- PostgreSQL 15+
- OpenAI API key

### 1. Clone the Repository

```bash
git clone https://github.com/govindp47/smarthire.git
cd smarthire
```

### 2. Backend Setup

```bash
cd backend

# Create virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Create .env file
cp .env.example .env
# Edit .env and add your credentials:
# - DATABASE_URL
# - SECRET_KEY
# - OPENAI_API_KEY

# Run migrations
alembic upgrade head

# Start server
uvicorn app.main:app --reload
```

Backend will be available at `http://localhost:8000`

### 3. Frontend Setup

```bash
cd frontend

# Install dependencies
npm install

# Create .env file
cp .env.example .env
# Edit if needed (defaults to http://localhost:8000)

# Start development server
npm run dev
```

Frontend will be available at `http://localhost:3000`

### 4. Access the Application

1. Open `http://localhost:3000`
2. Sign up for a new account
3. Create your first job posting
4. Upload resumes and let AI do the magic! ✨

---

## 📚 Documentation

- **API Documentation**: `http://localhost:8000/docs` (Swagger UI)
- **Database Schema**: See [docs/DATABASE_SCHEMA.md](docs/DATABASE_SCHEMA.md)
- **Architecture**: See [docs/ARCHITECTURE.md](docs/ARCHITECTURE.md)
- **Project State**: See [docs/PROJECT_STATE.md](docs/PROJECT_STATE.md)

---

## 🏗️ Project Structure

```
smarthire/
├── backend/
│   ├── app/
│   │   ├── api/routes/      # API endpoints
│   │   ├── core/            # Config, security, LLM instances
│   │   ├── models/          # SQLAlchemy models
│   │   ├── schemas/         # Pydantic schemas
│   │   ├── services/        # Business logic (parsing, scoring, RAG)
│   │   ├── database.py      # DB connection
│   │   └── main.py          # FastAPI app
│   ├── alembic/             # Database migrations
│   ├── uploads/             # Local file storage (gitignored)
│   ├── vector_store/        # ChromaDB data (gitignored)
│   └── requirements.txt
├── frontend/
│   ├── src/
│   │   ├── components/      # Reusable components
│   │   ├── context/         # React contexts
│   │   ├── lib/             # API client, utilities
│   │   ├── pages/           # Page components
│   │   └── App.jsx
│   └── package.json
└── docs/                    # Documentation
```

---

## 🔧 Configuration

### Environment Variables

#### Backend (.env)

```env
DATABASE_URL=postgresql+asyncpg://user:password@localhost:5432/smarthire_db
SECRET_KEY=your-secret-key-here
OPENAI_API_KEY=sk-...
EMBEDDING_MODEL=text-embedding-ada-002
VECTOR_STORE_PATH=./vector_store
CORS_ORIGINS=http://localhost:3000
```

#### Frontend (.env)

```env
VITE_API_BASE_URL=http://localhost:8000
```

---

## 🤖 AI Features Explained

### Resume Parsing Pipeline

1. **Text Extraction**: PDFs/DOCX → plain text (using pypdf/python-docx)
2. **LLM Parsing**: GPT-4o-mini extracts structured data (skills, experience, education)
3. **Storage**: Parsed data saved to PostgreSQL (JSONB columns)
4. **Embedding**: Text chunks → OpenAI embeddings → ChromaDB

### Scoring Algorithm

- **Skills Match (50%)**: Keyword matching + partial matching
- **Experience Level (25%)**: Years of experience vs job requirements
- **Semantic Similarity (25%)**: Cosine similarity of embeddings

### RAG Query System (LangChain 1.0+)

- Uses modern **LCEL (LangChain Expression Language)**
- No legacy chains (following latest LangChain recommendations)
- Singleton LLM instances for performance
- Conversation memory for follow-up questions

---

## 🙏 Acknowledgments

This project was built with the assistance of **Claude AI (Anthropic)** as a learning and development tool. Claude provided:

- Architecture guidance and best practices
- Code generation and iteration
- LangChain 1.0+ integration patterns
- Modern async Python and React patterns

**Transparency Statement**: AI assistance was used to accelerate development and learn new technologies. All code has been reviewed, understood, and can be explained by the developer. Claude served as a pair programming assistant to help implement industry-standard patterns and best practices.


---


<div align="center">

**Built with ❤️ using FastAPI, React, and AI**

⭐ Star this repo if you find it helpful!

</div>
