# SmartHire - Deployment Options Comparison

## Option 1: Simple All-in-One (RECOMMENDED for Free Tier)

### Architecture

```
EC2 Instance (t2.micro)
├── Docker: PostgreSQL
├── Docker: Backend
└── Docker: Frontend
```

### What You Need

- ✅ EC2 instance
- ✅ OpenAI API key
- ❌ No RDS
- ❌ No S3
- ❌ No IAM access keys

### Setup Steps

1. Launch EC2 instance
2. Install Docker
3. Clone repo
4. Create `.env` from `.env.simple.example`
5. Run `docker-compose up -d`

### .env File

```env
POSTGRES_USER=smarthire
POSTGRES_PASSWORD=secure-password
POSTGRES_DB=smarthire_db
SECRET_KEY=random-32-char-key
OPENAI_API_KEY=sk-your-key
CORS_ORIGINS=http://YOUR-EC2-IP
VITE_API_BASE_URL=http://YOUR-EC2-IP:8000
```

### File Storage

- Resumes stored in `/app/uploads` (Docker volume)
- Backed up with EC2 snapshots

### Docker Command

```bash
docker-compose up -d
```

### Pros

- ✅ Simplest setup
- ✅ Everything on one server
- ✅ No AWS credential management
- ✅ Free tier eligible

### Cons

- ⚠️ Database on same instance (less scalable)
- ⚠️ Files not in S3 (need manual backups)

### Best For

- Portfolio projects
- MVP/Demo
- Learning/Testing
- Free tier budget

---

## Option 2: Production with RDS + S3

### Architecture

```
EC2 Instance (t2.micro)
├── Docker: Backend → RDS PostgreSQL
└── Docker: Frontend

AWS RDS (db.t3.micro)
└── PostgreSQL Database

AWS S3
└── Resume Files
```

### What You Need

- ✅ EC2 instance
- ✅ RDS database
- ✅ S3 bucket
- ✅ IAM user with access keys
- ✅ OpenAI API key

### Setup Steps

1. Create RDS database
2. Create S3 bucket
3. Create IAM user & access keys
4. Launch EC2 instance
5. Install Docker
6. Clone repo
7. Create `.env` from `.env.production.example`
8. Run `docker-compose -f docker-compose.prod.yml up -d`

### .env File

```env
DATABASE_URL=postgresql+asyncpg://user:pass@rds-endpoint:5432/db
SECRET_KEY=random-32-char-key
OPENAI_API_KEY=sk-your-key
AWS_ACCESS_KEY_ID=AKIA...
AWS_SECRET_ACCESS_KEY=wJal...
AWS_REGION=us-east-1
S3_BUCKET_NAME=your-bucket
CORS_ORIGINS=http://YOUR-EC2-IP
VITE_API_BASE_URL=http://YOUR-EC2-IP:8000
```

### File Storage

- Resumes stored in S3
- Automatic versioning
- Highly available

### Docker Command

```bash
docker-compose -f docker-compose.prod.yml up -d
```

### Pros

- ✅ Managed database (auto backups)
- ✅ Scalable storage (S3)
- ✅ Database separate from app
- ✅ More production-ready

### Cons

- ⚠️ More complex setup
- ⚠️ Requires IAM credential management
- ⚠️ More AWS services to manage

### Best For

- Production deployments
- Scaling beyond MVP
- Professional projects
- When expecting growth

---

## Quick Decision Guide

### Choose OPTION 1 if

- ✅ First deployment / Learning
- ✅ Free tier priority
- ✅ Portfolio/Demo project
- ✅ Simple is better
- ✅ Don't want to manage credentials

### Choose OPTION 2 if

- ✅ Production app
- ✅ Expecting users/traffic
- ✅ Need scalability
- ✅ Want managed database
- ✅ Comfortable with AWS

---

## Cost Comparison (Monthly)

### Option 1: All-in-One

| Service | Cost |
|---------|------|
| EC2 t2.micro | FREE (750 hrs) |
| Total | **$0** |

### Option 2: RDS + S3

| Service | Cost |
|---------|------|
| EC2 t2.micro | FREE (750 hrs) |
| RDS db.t3.micro | FREE (750 hrs) |
| S3 (5GB) | FREE |
| Total | **$0** (within free tier) |

Both are free within AWS Free Tier limits!

---

## Migration Path

Start with **Option 1**, migrate to **Option 2** later:

```bash
# 1. Backup database from Docker
docker exec smarthire-postgres pg_dump -U smarthire smarthire_db > backup.sql

# 2. Create RDS database
# (follow AWS guide)

# 3. Restore to RDS
psql -h rds-endpoint -U smarthire smarthire_db < backup.sql

# 4. Update .env with RDS credentials

# 5. Switch to prod compose
docker-compose down
docker-compose -f docker-compose.prod.yml up -d
```

---

## Which docker-compose to use?

### For OPTION 1

```bash
docker-compose up -d
# Uses: docker-compose.yml
```

### For OPTION 2

```bash
docker-compose -f docker-compose.prod.yml up -d
# Uses: docker-compose.prod.yml
```
