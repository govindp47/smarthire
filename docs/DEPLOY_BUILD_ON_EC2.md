# Deployment: Build Directly on EC2

## SmartHire — Push Dockerfile to GitHub, Build on EC2

> **When to use:** Your EC2 instance has enough resources to build Docker images.
> **Problem with t2.micro:** 1 GB RAM is often not enough — images may fail to build.
> **Recommended for:** t2.medium or larger EC2 instances.

---

## How It Works

```
Local Machine          GitHub           EC2 Instance
     │                   │                   │
     │  git push         │                   │
     │──────────────────►│                   │
     │                   │   git clone/pull  │
     │                   │──────────────────►│
     │                   │                   │ docker-compose build
     │                   │                   │ (builds here)
     │                   │                   │ docker-compose up -d
     │                   │                   │ (runs here)
```

---

## Part 1: Prepare Locally

### What needs to be in your GitHub repo

```
smarthire/
├── backend/
│   ├── Dockerfile          ← required
│   ├── .dockerignore       ← required
│   └── ...
├── frontend/
│   ├── Dockerfile          ← required
│   ├── nginx.conf          ← required
│   ├── .dockerignore       ← required
│   └── ...
├── docker-compose.yml      ← used on EC2
├── .env.simple.example     ← template (no secrets)
└── ...
```

### Verify files exist locally

```bash
cd smarthire

ls backend/Dockerfile
ls frontend/Dockerfile
ls docker-compose.yml
ls .env.simple.example
```

### Commit and push everything

```bash
git add .
git commit -m "Add Docker setup for EC2 deployment"
git push origin main
```

---

## Part 2: Setup EC2

### Step 1: SSH into EC2

```bash
ssh -i ~/.ssh/smarthire-key.pem ubuntu@YOUR-EC2-PUBLIC-IP
```

### Step 2: Install Docker

```bash
# Update system
sudo apt update && sudo apt upgrade -y

# Install Docker using official script
curl -fsSL https://get.docker.com -o get-docker.sh
sudo sh get-docker.sh

# Add ubuntu user to docker group (so you don't need sudo)
sudo usermod -aG docker ubuntu

# Install Docker Compose
sudo curl -L \
    "https://github.com/docker/compose/releases/download/v2.20.0/docker-compose-$(uname -s)-$(uname -m)" \
    -o /usr/local/bin/docker-compose
sudo chmod +x /usr/local/bin/docker-compose

# IMPORTANT: logout and back in for group change to take effect
exit
```

```bash
# SSH back in
ssh -i ~/.ssh/smarthire-key.pem ubuntu@YOUR-EC2-PUBLIC-IP

# Verify
docker --version
docker-compose --version
```

### Step 3: Clone Repository

```bash
cd /home/ubuntu
git clone https://github.com/YOUR-USERNAME/smarthire.git
cd smarthire
```

### Step 4: Create .env File

```bash
# Copy template
cp .env.simple.example .env

# Edit with real values
nano .env
```

Fill in your actual values:

```env
# PostgreSQL (runs in Docker on this EC2)
POSTGRES_USER=smarthire
POSTGRES_PASSWORD=MyActualSecurePassword123!
POSTGRES_DB=smarthire_db

# Database URL (update with YOUR RDS endpoint)
DATABASE_URL=postgresql+asyncpg://smarthire:YOUR_RDS_PASSWORD@YOUR-RDS-ENDPOINT:5432/smarthire_db

# Security — generate with: openssl rand -hex 32
SECRET_KEY=paste-your-generated-key-here

# OpenAI
OPENAI_API_KEY=sk-your-actual-openai-key
EMBEDDING_MODEL=text-embedding-ada-002

# Leave blank — using local file storage, not S3
AWS_ACCESS_KEY_ID=
AWS_SECRET_ACCESS_KEY=
AWS_REGION=
S3_BUCKET_NAME=

# Replace with your actual EC2 public IP
CORS_ORIGINS=http://YOUR-EC2-PUBLIC-IP

# Replace with your actual EC2 public IP
VITE_API_BASE_URL=http://YOUR-EC2-PUBLIC-IP:8000

ENVIRONMENT=production
```

Save: `Ctrl+X` → `Y` → `Enter`

**Generate SECRET_KEY:**

```bash
openssl rand -hex 32
# Copy the output into your .env SECRET_KEY field
```

---

## Part 3: Build and Deploy

### Build images on EC2

```bash
cd /home/ubuntu/smarthire

# Build backend first
docker-compose build backend

# Then frontend
docker-compose build frontend
```

> ⚠️ **If you get "no space left on device" error:**
>
> ```bash
> # Clean Docker cache first
> docker system prune -a --volumes
> # Type 'y' to confirm
>
> # Then try building one at a time again
> docker-compose build backend
> docker-compose build frontend
> ```

### Start all services

```bash
docker-compose up -d
```

### Verify it's running

```bash
# Check container status
docker-compose ps

# Expected output:
# smarthire-postgres    Up (healthy)
# smarthire-backend     Up (healthy)
# smarthire-frontend    Up
```

### Check logs if something is wrong

```bash
# All services
docker-compose logs

# Specific service
docker-compose logs backend
docker-compose logs frontend
docker-compose logs postgres
```

---

## Part 4: Test

```bash
# Test backend health
curl http://localhost:8000/health
# Expected: {"status":"healthy","timestamp":"..."}

# Test frontend is serving
curl http://localhost:80
# Expected: HTML content
```

**In your browser:**

- Frontend: `http://YOUR-EC2-PUBLIC-IP`
- Backend API docs: `http://YOUR-EC2-PUBLIC-IP:8000/docs`

---

## Part 5: Updating the Application

When you push code changes:

```bash
# On EC2
cd /home/ubuntu/smarthire

# Pull latest code
git pull

# Rebuild changed services
docker-compose build backend    # if backend changed
docker-compose build frontend   # if frontend changed

# Restart with new images
docker-compose up -d
```

---

## Useful Maintenance Commands

```bash
# View live logs
docker-compose logs -f

# Restart a single service
docker-compose restart backend

# Stop everything (keeps data)
docker-compose down

# Stop and remove volumes (⚠️ deletes database!)
docker-compose down --volumes

# Check disk space
df -h

# Check Docker disk usage
docker system df

# Clean unused images/cache
docker system prune -f
```

---

## Why This Might Fail on t2.micro

The EC2 t2.micro has only **1 GB RAM**. Building Docker images (especially Python/Node.js) requires more:

```
Backend build:  ~1.5–2 GB RAM needed
Frontend build: ~1 GB RAM needed
t2.micro:       1 GB available ❌
```

**If builds fail, use Option 2 instead** (build locally, push to Docker Hub).
