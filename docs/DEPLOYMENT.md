# SmartHire - AWS Deployment Guide

Complete guide to deploying SmartHire on AWS with Docker.

---

## Architecture Overview

```
┌─────────────┐
│   Route 53  │ (Optional - Domain)
└──────┬──────┘
       │
┌──────▼──────────┐
│  Load Balancer  │ (Optional - For scaling)
└──────┬──────────┘
       │
┌──────▼──────────┐
│   EC2 Instance  │
│   - Frontend    │
│   - Backend     │
│   - Docker      │
└──────┬──────────┘
       │
       ├────────────┬─────────────┐
       │            │             │
┌──────▼──────┐ ┌──▼────────┐ ┌──▼──────┐
│     RDS     │ │    S3     │ │ Secrets │
│ PostgreSQL  │ │  Storage  │ │ Manager │
└─────────────┘ └───────────┘ └─────────┘
```

---

## Prerequisites

- AWS Account
- AWS CLI installed and configured
- SSH key pair for EC2
- Domain name (optional)
- OpenAI API key

---

## Step 1: Create RDS PostgreSQL Database

### 1.1 Create DB Subnet Group

```bash
aws rds create-db-subnet-group \
  --db-subnet-group-name smarthire-db-subnet \
  --db-subnet-group-description "SmartHire DB Subnet" \
  --subnet-ids subnet-xxx subnet-yyy \
  --tags "Key=Name,Value=smarthire-db-subnet"
```

### 1.2 Create Security Group for RDS

```bash
aws ec2 create-security-group \
  --group-name smarthire-rds-sg \
  --description "Security group for SmartHire RDS" \
  --vpc-id vpc-xxxxx

# Allow PostgreSQL from EC2 security group
aws ec2 authorize-security-group-ingress \
  --group-id sg-rds-xxxxx \
  --protocol tcp \
  --port 5432 \
  --source-group sg-ec2-xxxxx
```

### 1.3 Create RDS Instance

```bash
aws rds create-db-instance \
  --db-instance-identifier smarthire-postgres \
  --db-instance-class db.t3.micro \
  --engine postgres \
  --engine-version 15.3 \
  --master-username smarthire \
  --master-user-password 'YourSecurePassword123!' \
  --allocated-storage 20 \
  --db-subnet-group-name smarthire-db-subnet \
  --vpc-security-group-ids sg-rds-xxxxx \
  --backup-retention-period 7 \
  --publicly-accessible false \
  --storage-encrypted \
  --tags "Key=Name,Value=smarthire-postgres"
```

**Save the endpoint:** `smarthire-postgres.xxxxx.us-east-1.rds.amazonaws.com`

---

## Step 2: Create S3 Bucket for Resume Storage

### 2.1 Create S3 Bucket

```bash
aws s3 mb s3://smarthire-resumes-prod --region us-east-1

# Enable versioning
aws s3api put-bucket-versioning \
  --bucket smarthire-resumes-prod \
  --versioning-configuration Status=Enabled

# Enable encryption
aws s3api put-bucket-encryption \
  --bucket smarthire-resumes-prod \
  --server-side-encryption-configuration '{
    "Rules": [{
      "ApplyServerSideEncryptionByDefault": {
        "SSEAlgorithm": "AES256"
      }
    }]
  }'
```

### 2.2 Create IAM Policy for S3 Access

Create `s3-policy.json`:

```json
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Effect": "Allow",
      "Action": [
        "s3:PutObject",
        "s3:GetObject",
        "s3:DeleteObject",
        "s3:ListBucket"
      ],
      "Resource": [
        "arn:aws:s3:::smarthire-resumes-prod",
        "arn:aws:s3:::smarthire-resumes-prod/*"
      ]
    }
  ]
}
```

```bash
aws iam create-policy \
  --policy-name SmartHireS3Access \
  --policy-document file://s3-policy.json
```

---

## Step 3: Launch EC2 Instance

### 3.1 Create Security Group

```bash
aws ec2 create-security-group \
  --group-name smarthire-ec2-sg \
  --description "Security group for SmartHire EC2" \
  --vpc-id vpc-xxxxx

# Allow HTTP
aws ec2 authorize-security-group-ingress \
  --group-id sg-ec2-xxxxx \
  --protocol tcp \
  --port 80 \
  --cidr 0.0.0.0/0

# Allow HTTPS
aws ec2 authorize-security-group-ingress \
  --group-id sg-ec2-xxxxx \
  --protocol tcp \
  --port 443 \
  --cidr 0.0.0.0/0

# Allow SSH (restrict to your IP)
aws ec2 authorize-security-group-ingress \
  --group-id sg-ec2-xxxxx \
  --protocol tcp \
  --port 22 \
  --cidr YOUR_IP/32
```

### 3.2 Create IAM Role for EC2

```bash
# Create trust policy
cat > ec2-trust-policy.json << EOF
{
  "Version": "2012-10-17",
  "Statement": [{
    "Effect": "Allow",
    "Principal": {"Service": "ec2.amazonaws.com"},
    "Action": "sts:AssumeRole"
  }]
}
EOF

# Create role
aws iam create-role \
  --role-name SmartHireEC2Role \
  --assume-role-policy-document file://ec2-trust-policy.json

# Attach S3 policy
aws iam attach-role-policy \
  --role-name SmartHireEC2Role \
  --policy-arn arn:aws:iam::YOUR_ACCOUNT:policy/SmartHireS3Access

# Create instance profile
aws iam create-instance-profile \
  --instance-profile-name SmartHireEC2Profile

aws iam add-role-to-instance-profile \
  --instance-profile-name SmartHireEC2Profile \
  --role-name SmartHireEC2Role
```

### 3.3 Launch EC2 Instance

```bash
aws ec2 run-instances \
  --image-id ami-0c55b159cbfafe1f0 \
  --count 1 \
  --instance-type t3.medium \
  --key-name your-key-pair \
  --security-group-ids sg-ec2-xxxxx \
  --subnet-id subnet-xxxxx \
  --iam-instance-profile Name=SmartHireEC2Profile \
  --block-device-mappings '[{"DeviceName":"/dev/xvda","Ebs":{"VolumeSize":30,"VolumeType":"gp3"}}]' \
  --tag-specifications 'ResourceType=instance,Tags=[{Key=Name,Value=SmartHire-Production}]'
```

---

## Step 4: Setup EC2 Instance

### 4.1 SSH into Instance

```bash
ssh -i your-key.pem ubuntu@ec2-xxx-xxx-xxx-xxx.compute.amazonaws.com
```

### 4.2 Install Docker

```bash
# Update system
sudo apt update && sudo apt upgrade -y

# Install Docker
curl -fsSL https://get.docker.com -o get-docker.sh
sudo sh get-docker.sh

# Add user to docker group
sudo usermod -aG docker ubuntu

# Install Docker Compose
sudo curl -L "https://github.com/docker/compose/releases/download/v2.20.0/docker-compose-$(uname -s)-$(uname -m)" -o /usr/local/bin/docker-compose
sudo chmod +x /usr/local/bin/docker-compose

# Verify installation
docker --version
docker-compose --version
```

### 4.3 Clone Repository

```bash
cd /home/ubuntu
git clone https://github.com/govindp47/smarthire.git
cd smarthire
```

### 4.4 Create Production Environment File

```bash
nano .env
```

Add:

```env
# Database (RDS Endpoint)
DATABASE_URL=postgresql+asyncpg://smarthire:YourSecurePassword123!@smarthire-postgres.xxxxx.us-east-1.rds.amazonaws.com:5432/smarthire_db

# Security
SECRET_KEY=generate_a_secure_random_key_here_at_least_32_chars

# OpenAI
OPENAI_API_KEY=sk-your-openai-api-key

# AWS
AWS_REGION=us-east-1
S3_BUCKET_NAME=smarthire-resumes-prod

# CORS (your domain)
CORS_ORIGINS=https://yourdomain.com,https://www.yourdomain.com

# Frontend
VITE_API_BASE_URL=https://yourdomain.com
```

---

## Step 5: Deploy with Docker Compose

### 5.1 Build and Start Services

```bash
# Build images
docker-compose -f docker-compose.prod.yml build

# Start services
docker-compose -f docker-compose.prod.yml up -d

# Check logs
docker-compose -f docker-compose.prod.yml logs -f
```

### 5.2 Verify Deployment

```bash
# Check running containers
docker ps

# Test backend
curl http://localhost:8000/docs

# Test frontend
curl http://localhost:80
```

---

## Step 6: Setup HTTPS with Let's Encrypt (Optional)

### 6.1 Install Certbot

```bash
sudo apt install certbot python3-certbot-nginx -y
```

### 6.2 Get SSL Certificate

```bash
sudo certbot --nginx -d yourdomain.com -d www.yourdomain.com
```

### 6.3 Auto-renewal

```bash
# Test renewal
sudo certbot renew --dry-run

# Certbot automatically sets up cron job
```

---

## Step 7: Setup Monitoring & Logging

### 7.1 CloudWatch Logs (Optional)

```bash
# Install CloudWatch agent
wget https://s3.amazonaws.com/amazoncloudwatch-agent/ubuntu/amd64/latest/amazon-cloudwatch-agent.deb
sudo dpkg -i amazon-cloudwatch-agent.deb
```

### 7.2 Docker Logs

```bash
# View logs
docker-compose -f docker-compose.prod.yml logs -f backend
docker-compose -f docker-compose.prod.yml logs -f frontend

# Export logs
docker-compose -f docker-compose.prod.yml logs > deployment.log
```

---

## Step 8: Backup Strategy

### 8.1 RDS Automated Backups

Already configured with 7-day retention. To create manual snapshot:

```bash
aws rds create-db-snapshot \
  --db-instance-identifier smarthire-postgres \
  --db-snapshot-identifier smarthire-backup-$(date +%Y%m%d)
```

### 8.2 S3 Versioning

Already enabled. Files are automatically versioned.

### 8.3 Vector Store Backup

```bash
# Create backup script
cat > /home/ubuntu/backup-vector-store.sh << 'EOF'
#!/bin/bash
BACKUP_DIR="/home/ubuntu/backups/vector_store"
mkdir -p $BACKUP_DIR
docker cp smarthire-backend-prod:/app/vector_store $BACKUP_DIR/vector_store_$(date +%Y%m%d)
# Upload to S3
aws s3 sync $BACKUP_DIR s3://smarthire-resumes-prod/backups/vector_store/
EOF

chmod +x /home/ubuntu/backup-vector-store.sh

# Add to crontab (daily at 2 AM)
(crontab -l 2>/dev/null; echo "0 2 * * * /home/ubuntu/backup-vector-store.sh") | crontab -
```

---

## Maintenance Commands

```bash
# Update application
cd /home/ubuntu/smarthire
git pull
docker-compose -f docker-compose.prod.yml build
docker-compose -f docker-compose.prod.yml up -d

# Restart services
docker-compose -f docker-compose.prod.yml restart

# View resource usage
docker stats

# Clean up old images
docker system prune -a
```

---

## Troubleshooting

### Database Connection Issues

```bash
# Test connection from EC2
docker exec smarthire-backend-prod python -c "
from sqlalchemy import create_engine
engine = create_engine('postgresql://...')
engine.connect()
"
```

### High Memory Usage

```bash
# Check memory
free -h

# Restart containers
docker-compose -f docker-compose.prod.yml restart
```

### Logs Not Showing

```bash
# Check container status
docker ps -a

# View detailed logs
docker logs smarthire-backend-prod --tail 100
```

---

## Cost Estimation (Monthly)

| Service | Configuration | Estimated Cost |
|---------|--------------|----------------|
| EC2 t3.medium | On-demand | ~$30 |
| RDS db.t3.micro | PostgreSQL 15 | ~$15 |
| S3 | 50GB storage | ~$1 |
| Data Transfer | 100GB/month | ~$9 |
| **Total** | | **~$55/month** |

---

## Security Checklist

- [x] RDS not publicly accessible
- [x] Security groups properly configured
- [x] IAM roles with least privilege
- [x] S3 bucket encryption enabled
- [x] SSL/TLS enabled (HTTPS)
- [x] Environment variables secured
- [x] Regular backups configured
- [x] Monitoring enabled

---

## Next Steps

1. ✅ Setup domain with Route 53
2. ✅ Configure CloudFront (CDN)
3. ✅ Add WAF for security
4. ✅ Setup CI/CD with GitHub Actions
5. ✅ Add application monitoring (DataDog/Sentry)

---

**Deployment Complete!** 🚀

Your SmartHire application is now running on AWS in production.
