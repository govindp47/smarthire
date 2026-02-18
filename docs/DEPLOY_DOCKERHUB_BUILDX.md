# Deployment: Build Locally → Docker Hub → EC2

## SmartHire — Cross-Platform Build with docker buildx

> **When to use:** EC2 t2.micro doesn't have enough RAM to build images.
> **Why buildx:** Mac (M1/M2/M3) is `arm64`, EC2 Ubuntu is `amd64`. Without buildx,
> images built on Mac are incompatible with EC2.
> **This is the recommended approach for t2.micro + Mac.**

---

## How It Works

```
Mac (arm64)                Docker Hub         EC2 (amd64/Linux)
     │                         │                     │
     │  buildx --platform      │                     │
     │  linux/amd64            │                     │
     │  (builds FOR amd64      │                     │
     │   even on arm64 Mac)    │                     │
     │                         │                     │
     │  docker push            │                     │
     │────────────────────────►│                     │
     │                         │   docker pull       │
     │                         │◄────────────────────│
     │                         │                     │
     │                         │  docker-compose up  │
     │                         │  (no build needed!) │
```

---

## Part 1: One-Time Setup (Local Mac)

### Step 1: Create Docker Hub Account

1. Go to <https://hub.docker.com/signup>
2. Sign up for free account
3. Verify email
4. Save your username — you'll need it throughout

### Step 2: Setup buildx on Mac

```bash
# Create a new builder that supports cross-platform
docker buildx create --name smarthire-builder --use

# Start and inspect the builder
docker buildx inspect --bootstrap

# Verify linux/amd64 is listed under platforms
docker buildx ls
```

Expected output shows:

```
NAME/NODE              PLATFORMS
smarthire-builder *    linux/amd64, linux/arm64, linux/arm/v7, ...
```

---

## Part 2: Build & Push Images (Local Mac)

### Option A: Using the Build Script (Recommended)

```bash
cd smarthire

# Make executable (first time only)
chmod +x scripts/build-and-push.sh

# Run it — handles everything
./scripts/build-and-push.sh
```

The script will:

1. Ask for your Docker Hub username
2. Login to Docker Hub
3. Create/reuse the buildx builder
4. Build backend for `linux/amd64` (EC2 compatible)
5. Build frontend for `linux/amd64` (EC2 compatible)
6. Push both to Docker Hub
7. Update `docker-compose.ec2.yml` with your username automatically

---

### Option B: Manual Commands

```bash
cd smarthire

# Step 1: Login to Docker Hub
docker login
# Enter username and password

# Step 2: Setup builder (if not done)
docker buildx create --name smarthire-builder --use
docker buildx inspect --bootstrap

# Step 3: Build & push backend for linux/amd64
docker buildx build \
    --platform linux/amd64 \
    --tag YOUR_DOCKERHUB_USERNAME/smarthire-backend:latest \
    --push \
    ./backend

# Step 4: Build & push frontend for linux/amd64
docker buildx build \
    --platform linux/amd64 \
    --tag YOUR_DOCKERHUB_USERNAME/smarthire-frontend:latest \
    --push \
    ./frontend
```

> ✅ `--push` builds AND pushes in one step — no separate `docker push` needed.

---

### Verify Images on Docker Hub

1. Go to <https://hub.docker.com>
2. Login → You should see:
   - `YOUR_USERNAME/smarthire-backend`
   - `YOUR_USERNAME/smarthire-frontend`
3. Both should show architecture: `amd64`

---

## Part 3: Update docker-compose.ec2.yml

If you ran the script, this is already done automatically.

If you ran manual commands, edit `docker-compose.ec2.yml`:

```bash
# Replace the placeholder with your actual Docker Hub username
sed -i '' 's|YOUR_DOCKERHUB_USERNAME|youractualusername|g' docker-compose.ec2.yml
```

Or edit manually — find these lines and replace:

```yaml
# Change this:
image: YOUR_DOCKERHUB_USERNAME/smarthire-backend:latest
image: YOUR_DOCKERHUB_USERNAME/smarthire-frontend:latest

# To this:
image: youractualusername/smarthire-backend:latest
image: youractualusername/smarthire-frontend:latest
```

### Push the updated file to GitHub

```bash
git add docker-compose.ec2.yml
git commit -m "Update Docker Hub username in ec2 compose file"
git push
```

---

## Part 4: Setup EC2 and Deploy

### Step 1: SSH into EC2

```bash
ssh -i ~/.ssh/smarthire-key.pem ubuntu@YOUR-EC2-PUBLIC-IP
```

### Step 2: Install Docker on EC2

```bash
# Update system
sudo apt update && sudo apt upgrade -y

# Install Docker
curl -fsSL https://get.docker.com -o get-docker.sh
sudo sh get-docker.sh

# Add user to docker group
sudo usermod -aG docker ubuntu

# Install Docker Compose
sudo curl -L \
    "https://github.com/docker/compose/releases/download/v2.20.0/docker-compose-$(uname -s)-$(uname -m)" \
    -o /usr/local/bin/docker-compose
sudo chmod +x /usr/local/bin/docker-compose

# Logout and back in
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
git clone https://github.com/YOUR-GITHUB-USERNAME/smarthire.git
cd smarthire
```

### Step 4: Create .env File

```bash
cp .env.simple.example .env
nano .env
```

Fill in your real values:

```env
POSTGRES_USER=smarthire
POSTGRES_PASSWORD=MyActualSecurePassword123!
POSTGRES_DB=smarthire_db
SECRET_KEY=paste-key-generated-by-openssl
OPENAI_API_KEY=sk-your-actual-key
AWS_ACCESS_KEY_ID=
AWS_SECRET_ACCESS_KEY=
AWS_REGION=
S3_BUCKET_NAME=
CORS_ORIGINS=http://YOUR-EC2-PUBLIC-IP
VITE_API_BASE_URL=http://YOUR-EC2-PUBLIC-IP:8000
ENVIRONMENT=production
```

Generate SECRET_KEY:

```bash
openssl rand -hex 32
```

Save: `Ctrl+X` → `Y` → `Enter`

### Step 5: Pull Pre-built Images from Docker Hub

```bash
# No building needed — just download!
docker pull YOUR_DOCKERHUB_USERNAME/smarthire-backend:latest
docker pull YOUR_DOCKERHUB_USERNAME/smarthire-frontend:latest
```

This is fast (~1–2 minutes) because it's just downloading, not building.

### Step 6: Start All Services

```bash
docker-compose -f docker-compose.ec2.yml up -d
```

### Step 7: Verify

```bash
# Check status
docker-compose -f docker-compose.ec2.yml ps

# Check logs
docker-compose -f docker-compose.ec2.yml logs

# Test backend
curl http://localhost:8000/health
```

---

## Part 5: Test in Browser

- **Frontend:** `http://YOUR-EC2-PUBLIC-IP`
- **Backend docs:** `http://YOUR-EC2-PUBLIC-IP:8000/docs`

---

## Part 6: Updating the Application

When you make code changes:

### On Mac (local)

```bash
cd smarthire

# Rebuild for linux/amd64 and push
docker buildx build \
    --platform linux/amd64 \
    --tag YOUR_USERNAME/smarthire-backend:latest \
    --push \
    ./backend

# Or rebuild both using the script
./scripts/build-and-push.sh
```

### On EC2

```bash
cd /home/ubuntu/smarthire

# Pull latest code (if any config files changed)
git pull

# Pull new images
docker pull YOUR_USERNAME/smarthire-backend:latest
docker pull YOUR_USERNAME/smarthire-frontend:latest

# Restart with new images
docker-compose -f docker-compose.ec2.yml down
docker-compose -f docker-compose.ec2.yml up -d
```

---

## Useful Maintenance Commands (on EC2)

```bash
# View live logs
docker-compose -f docker-compose.ec2.yml logs -f

# Restart a single service
docker-compose -f docker-compose.ec2.yml restart backend

# Stop everything (data is preserved in volumes)
docker-compose -f docker-compose.ec2.yml down

# Check disk usage
docker system df
df -h
```

---

## Why `--platform linux/amd64`?

| Machine | Architecture |
|---------|-------------|
| Mac M1/M2/M3 | arm64 |
| EC2 Ubuntu t2.micro | amd64 (x86_64) |

Without `--platform linux/amd64`, Docker builds for your Mac's native `arm64`.
When EC2 tries to run an `arm64` image on its `amd64` hardware:

```
exec /usr/local/bin/python: exec format error ❌
```

With `--platform linux/amd64`, the image is built for EC2's architecture even though
you're building on a Mac. EC2 runs it perfectly. ✅

---

## Summary: 3 Commands That Matter

```bash
# 1. On Mac: build and push (cross-platform)
./scripts/build-and-push.sh

# 2. On EC2: pull images (no build needed)
docker pull YOUR_USERNAME/smarthire-backend:latest
docker pull YOUR_USERNAME/smarthire-frontend:latest

# 3. On EC2: start everything
docker-compose -f docker-compose.ec2.yml up -d
```
