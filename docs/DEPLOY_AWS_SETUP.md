# AWS Setup Guide: EC2 + RDS + S3

## SmartHire Deployment Reference

> **Context:** Free Tier account, deploying SmartHire (FastAPI + React + PostgreSQL).
> Covers both AWS Console (browser) and AWS CLI (terminal) approaches side by side.

---

## Prerequisites

- AWS Free Tier account
- AWS CLI installed locally (for CLI approach)
- SSH key pair (created in Step 1)

### Install & Configure AWS CLI (CLI approach only)

```bash
# Mac
brew install awscli

# Verify
aws --version

# Configure with your credentials
aws configure
# AWS Access Key ID: (from IAM → Your user → Security credentials)
# AWS Secret Access Key: (same place)
# Default region: us-east-1   ← pick region closest to you
# Default output format: json
```

---

## Step 1: Create SSH Key Pair

> You need this to SSH into EC2 later. Do this first.

### Console

1. Services → EC2 → **Key Pairs** (left sidebar, under "Network & Security")
2. **Create key pair**
   - Name: `smarthire-key`
   - Type: RSA
   - Format: `.pem` (Mac/Linux) or `.ppk` (Windows/PuTTY)
3. Click **Create key pair** — file downloads automatically

### CLI

```bash
aws ec2 create-key-pair \
    --key-name smarthire-key \
    --query 'KeyMaterial' \
    --output text > ~/.ssh/smarthire-key.pem
```

### After downloading (both approaches)

```bash
# Set correct permissions — required or SSH will refuse the key
chmod 400 ~/.ssh/smarthire-key.pem
```

---

## Step 2: Create RDS PostgreSQL Database

### Step 2a: Create Security Group for RDS

#### Console

1. Services → EC2 → **Security Groups**
2. **Create security group**
   - Name: `smarthire-rds-sg`
   - Description: `Security group for SmartHire PostgreSQL`
   - VPC: Default
3. **Inbound rules** → Add rule:
   - Type: PostgreSQL | Port: 5432 | Source: **My IP** *(temporary — we'll fix this after EC2 is created)*
4. **Create security group**
5. Note the Security Group ID: `sg-xxxxxxxxx`

#### CLI

```bash
# Get your default VPC ID first
VPC_ID=$(aws ec2 describe-vpcs \
    --filters "Name=is-default,Values=true" \
    --query 'Vpcs[0].VpcId' \
    --output text)

# Create security group
RDS_SG=$(aws ec2 create-security-group \
    --group-name smarthire-rds-sg \
    --description "Security group for SmartHire PostgreSQL" \
    --vpc-id $VPC_ID \
    --query 'GroupId' \
    --output text)

echo "RDS Security Group: $RDS_SG"

# Add inbound rule (temporary: your IP)
MY_IP=$(curl -s https://checkip.amazonaws.com)
aws ec2 authorize-security-group-ingress \
    --group-id $RDS_SG \
    --protocol tcp \
    --port 5432 \
    --cidr $MY_IP/32
```

### Step 2b: Create RDS Instance

#### Console

1. Services → **RDS** → **Create database**
2. Settings:
   - **Engine:** PostgreSQL | **Version:** 15.x
   - **Template:** ✅ **Free tier**
   - **DB instance identifier:** `smarthire-postgres`
   - **Master username:** `smarthire`
   - **Master password:** *(create strong password — save it!)*
3. **Instance config:** `db.t3.micro` (free tier)
4. **Storage:** 20 GiB gp2 | **Disable** storage autoscaling
5. **Connectivity:**
   - Public access: **No**
   - Security group: `smarthire-rds-sg`
6. **Additional config:**
   - Initial database name: `smarthire_db`
   - Backup retention: 7 days
7. **Create database** — takes 5–10 minutes

#### CLI

```bash
# Get a subnet group (uses default subnets)
# First list available subnets in your VPC
SUBNETS=$(aws ec2 describe-subnets \
    --filters "Name=vpc-id,Values=$VPC_ID" \
    --query 'Subnets[*].SubnetId' \
    --output text | tr '\t' ' ')

# Create DB subnet group
aws rds create-db-subnet-group \
    --db-subnet-group-name smarthire-db-subnet \
    --db-subnet-group-description "SmartHire DB Subnet Group" \
    --subnet-ids $SUBNETS

# Create RDS instance
aws rds create-db-instance \
    --db-instance-identifier smarthire-postgres \
    --db-instance-class db.t3.micro \
    --engine postgres \
    --engine-version 15.4 \
    --master-username smarthire \
    --master-user-password 'YourSecurePassword123!' \
    --allocated-storage 20 \
    --db-subnet-group-name smarthire-db-subnet \
    --vpc-security-group-ids $RDS_SG \
    --backup-retention-period 7 \
    --no-publicly-accessible \
    --storage-encrypted \
    --db-name smarthire_db \
    --no-multi-az

# Wait until available (5-10 minutes)
aws rds wait db-instance-available \
    --db-instance-identifier smarthire-postgres

# Get the endpoint
aws rds describe-db-instances \
    --db-instance-identifier smarthire-postgres \
    --query 'DBInstances[0].Endpoint.Address' \
    --output text
```

### Save the RDS endpoint

```
RDS Endpoint: smarthire-postgres.xxxxx.us-east-1.rds.amazonaws.com
Database:     smarthire_db
Username:     smarthire
Password:     YourSecurePassword123!
```

---

## Step 3: Create S3 Bucket

### Step 3a: Create the bucket

#### Console

1. Services → **S3** → **Create bucket**
   - Name: `smarthire-resumes-yourname-2026` *(must be globally unique!)*
   - Region: Same as everything else
   - Block all public access: ✅ Yes
   - Bucket Versioning: Enable
   - Default encryption: Enable (SSE-S3)
2. **Create bucket**

#### CLI

```bash
BUCKET_NAME="smarthire-resumes-yourname-2026"
REGION="us-east-1"

# Create bucket
aws s3api create-bucket \
    --bucket $BUCKET_NAME \
    --region $REGION

# Enable versioning
aws s3api put-bucket-versioning \
    --bucket $BUCKET_NAME \
    --versioning-configuration Status=Enabled

# Enable encryption
aws s3api put-bucket-encryption \
    --bucket $BUCKET_NAME \
    --server-side-encryption-configuration '{
        "Rules": [{
            "ApplyServerSideEncryptionByDefault": {
                "SSEAlgorithm": "AES256"
            }
        }]
    }'

# Block public access
aws s3api put-public-access-block \
    --bucket $BUCKET_NAME \
    --public-access-block-configuration \
        "BlockPublicAcls=true,IgnorePublicAcls=true,BlockPublicPolicy=true,RestrictPublicBuckets=true"
```

### Step 3b: Create IAM Policy for S3 Access

#### Console

1. Services → IAM → **Policies** → **Create policy**
2. Click **JSON** tab, paste:

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
        "arn:aws:s3:::smarthire-resumes-yourname-2026",
        "arn:aws:s3:::smarthire-resumes-yourname-2026/*"
      ]
    }
  ]
}
```

3. Name: `SmartHireS3Access` → **Create policy**

#### CLI

```bash
# Create policy document
cat > /tmp/s3-policy.json << EOF
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
        "arn:aws:s3:::$BUCKET_NAME",
        "arn:aws:s3:::$BUCKET_NAME/*"
      ]
    }
  ]
}
EOF

ACCOUNT_ID=$(aws sts get-caller-identity --query Account --output text)

aws iam create-policy \
    --policy-name SmartHireS3Access \
    --policy-document file:///tmp/s3-policy.json

# Note the policy ARN from output:
# arn:aws:iam::123456789012:policy/SmartHireS3Access
```

---

## Step 4: Launch EC2 Instance

### Step 4a: Create Security Group for EC2

#### Console

1. Services → EC2 → **Security Groups** → **Create security group**
   - Name: `smarthire-ec2-sg`
   - Description: `Security group for SmartHire EC2`
2. **Inbound rules** — add 3 rules:

| Type | Port | Source |
|------|------|--------|
| SSH | 22 | My IP |
| HTTP | 80 | Anywhere (0.0.0.0/0) |
| Custom TCP | 8000 | Anywhere (0.0.0.0/0) |

1. **Create security group** — note the ID: `sg-yyyyyyyyy`

#### CLI

```bash
EC2_SG=$(aws ec2 create-security-group \
    --group-name smarthire-ec2-sg \
    --description "Security group for SmartHire EC2" \
    --vpc-id $VPC_ID \
    --query 'GroupId' \
    --output text)

echo "EC2 Security Group: $EC2_SG"

MY_IP=$(curl -s https://checkip.amazonaws.com)

# SSH - your IP only
aws ec2 authorize-security-group-ingress \
    --group-id $EC2_SG --protocol tcp --port 22 --cidr $MY_IP/32

# HTTP - public
aws ec2 authorize-security-group-ingress \
    --group-id $EC2_SG --protocol tcp --port 80 --cidr 0.0.0.0/0

# Backend API - public
aws ec2 authorize-security-group-ingress \
    --group-id $EC2_SG --protocol tcp --port 8000 --cidr 0.0.0.0/0
```

### Step 4b: Update RDS Security Group to allow EC2

#### Console

1. Security Groups → Select `smarthire-rds-sg`
2. Inbound rules → **Edit inbound rules**
3. Delete the "My IP" rule
4. Add new rule:
   - Type: PostgreSQL | Port: 5432 | Source: select `smarthire-ec2-sg`
5. **Save rules**

#### CLI

```bash
# Remove the temporary My IP rule
aws ec2 revoke-security-group-ingress \
    --group-id $RDS_SG \
    --protocol tcp \
    --port 5432 \
    --cidr $MY_IP/32

# Add EC2 security group as source instead
aws ec2 authorize-security-group-ingress \
    --group-id $RDS_SG \
    --protocol tcp \
    --port 5432 \
    --source-group $EC2_SG
```

### Step 4c: Create IAM Role for EC2 (to access S3)

#### Console

1. IAM → **Roles** → **Create role**
2. Trusted entity: **AWS service** | Use case: **EC2** → Next
3. Search and select `SmartHireS3Access` → Next
4. Role name: `SmartHireEC2Role` → **Create role**

#### CLI

```bash
# Trust policy
cat > /tmp/ec2-trust.json << 'EOF'
{
  "Version": "2012-10-17",
  "Statement": [{
    "Effect": "Allow",
    "Principal": { "Service": "ec2.amazonaws.com" },
    "Action": "sts:AssumeRole"
  }]
}
EOF

aws iam create-role \
    --role-name SmartHireEC2Role \
    --assume-role-policy-document file:///tmp/ec2-trust.json

aws iam attach-role-policy \
    --role-name SmartHireEC2Role \
    --policy-arn arn:aws:iam::$ACCOUNT_ID:policy/SmartHireS3Access

aws iam create-instance-profile \
    --instance-profile-name SmartHireEC2Profile

aws iam add-role-to-instance-profile \
    --instance-profile-name SmartHireEC2Profile \
    --role-name SmartHireEC2Role
```

### Step 4d: Create IAM User for Application (to access S3)

#### Console

1. IAM → **Users** → **Create user**
2. User name: `smarthire-app-user` → Next
3. Permissions: **"Attach policies directly"** → `SmartHireS3Access` → check box → Next
4. **Create user**
5. `smarthire-app-user` → **"Security credentials"** → **"Access keys"** → **"Create access key"**
6. Use case: **"Application running outside AWS"** or **"Other"** → Next
7. Description tag: `SmartHire EC2 App`
8. **"Create access key"**

### Save Credentials

```
Access Key ID:      AKIAIOSFODNN7EXAMPLE
Secret Access Key:  wJalrXUtnFEMI/K7MDENG/bPxRfiCYEXAMPLEKEY
```

### Step 4e: Launch EC2 Instance

#### Console

1. Services → EC2 → **Launch instances**
   - Name: `SmartHire-Production`
   - AMI: **Ubuntu Server 22.04 LTS** (Free tier eligible)
   - Instance type: **t2.micro** (Free tier eligible)
   - Key pair: `smarthire-key`
2. Network settings → **Edit**:
   - Auto-assign public IP: **Enable**
   - Security group: `smarthire-ec2-sg`
3. Storage: **30 GiB gp3**
4. Advanced details → IAM instance profile: `SmartHireEC2Profile`
5. **Launch instance** — takes 2–3 minutes
6. Click instance ID → note **Public IPv4 address**

#### CLI

```bash
# Get Ubuntu 22.04 AMI for your region
AMI_ID=$(aws ec2 describe-images \
    --owners 099720109477 \
    --filters \
        "Name=name,Values=ubuntu/images/hvm-ssd/ubuntu-jammy-22.04-amd64-server-*" \
        "Name=state,Values=available" \
    --query 'sort_by(Images, &CreationDate)[-1].ImageId' \
    --output text)

echo "AMI: $AMI_ID"

# Get default subnet
SUBNET_ID=$(aws ec2 describe-subnets \
    --filters "Name=vpc-id,Values=$VPC_ID" "Name=default-for-az,Values=true" \
    --query 'Subnets[0].SubnetId' \
    --output text)

# Launch instance
INSTANCE_ID=$(aws ec2 run-instances \
    --image-id $AMI_ID \
    --count 1 \
    --instance-type t2.micro \
    --key-name smarthire-key \
    --security-group-ids $EC2_SG \
    --subnet-id $SUBNET_ID \
    --iam-instance-profile Name=SmartHireEC2Profile \
    --associate-public-ip-address \
    --block-device-mappings '[{
        "DeviceName":"/dev/sda1",
        "Ebs":{"VolumeSize":30,"VolumeType":"gp3"}
    }]' \
    --tag-specifications 'ResourceType=instance,Tags=[{Key=Name,Value=SmartHire-Production}]' \
    --query 'Instances[0].InstanceId' \
    --output text)

echo "Instance ID: $INSTANCE_ID"

# Wait until running
aws ec2 wait instance-running --instance-ids $INSTANCE_ID

# Get public IP
EC2_IP=$(aws ec2 describe-instances \
    --instance-ids $INSTANCE_ID \
    --query 'Reservations[0].Instances[0].PublicIpAddress' \
    --output text)

echo "EC2 Public IP: $EC2_IP"
```

---

## Step 5: Connect to EC2

```bash
ssh -i ~/.ssh/smarthire-key.pem ubuntu@YOUR-EC2-PUBLIC-IP

# First time: type 'yes' when asked about fingerprint
```

**If "Permission denied":**

```bash
chmod 400 ~/.ssh/smarthire-key.pem
```

---

## Quick Reference: Save These Values

```
EC2 Public IP:    xx.xx.xx.xx
RDS Endpoint:     smarthire-postgres.xxxxx.us-east-1.rds.amazonaws.com
RDS Database:     smarthire_db
RDS Username:     smarthire
RDS Password:     YourSecurePassword123!
S3 Bucket:        smarthire-resumes-yourname-2026
Region:           us-east-1
SSH Key:          ~/.ssh/smarthire-key.pem
```

---

## Free Tier Limits (Stay Within These!)

| Service | Free Limit | Our Usage |
|---------|-----------|-----------|
| EC2 t2.micro | 750 hrs/month | ~744 hrs (24/7) ✅ |
| RDS db.t3.micro | 750 hrs/month | ~744 hrs (24/7) ✅ |
| RDS storage | 20 GB | 20 GB ✅ |
| S3 storage | 5 GB | Depends on resumes |
| S3 requests | 20K GET, 2K PUT | Light usage ✅ |
| Data transfer out | 15 GB/month | Light usage ✅ |

> ⚠️ **Stop (don't terminate) instances** when not using them to save hours.
