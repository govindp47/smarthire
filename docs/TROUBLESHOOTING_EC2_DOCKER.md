# EC2 + Docker Troubleshooting Guide

## SmartHire — Debugging Container Issues on Small EC2 Instances

> **Context:** Common issues when running Docker on t2.micro/t3.micro EC2 instances (1 GB RAM).
> Based on real production debugging experience.

---

## Overview

### Common Symptoms

- 🔴 Containers randomly exit with code 137
- 🔴 EC2 instance becomes unresponsive / freezes
- 🔴 Services work initially but crash under load
- 🔴 `docker ps` shows containers as "Restarting"
- 🔴 SSH connections hang or timeout
- 🔴 Build processes fail with "no space left on device"

### Root Causes (In Order of Frequency)

1. **Out of Memory (OOM)** — 80% of issues
2. **No swap configured** — Makes OOM worse
3. **Too many workers** — Multiplies memory usage
4. **Docker build cache** — Fills disk
5. **Healthcheck misconfiguration** — False alarms

---

# Debugging Workflow

## Step 1: Check EC2 Instance Health

### Check Memory Usage

**Command:**

```bash
free -h
```

**Example output:**

```
              total        used        free      shared  buff/cache   available
Mem:          974Mi       856Mi        45Mi       1.0Mi        72Mi        28Mi
Swap:            0B          0B          0B
```

**Red flags:**

- ⚠️ `Swap: 0B` — No swap configured (dangerous!)
- ⚠️ `Available < 100MB` — OOM imminent
- ⚠️ `Used > 90%` — High memory pressure

---

### Check CPU and Real-Time Resources

**Command:**

```bash
htop
```

**If not installed:**

```bash
sudo apt update && sudo apt install -y htop
```

**What to look for:**

- CPU usage consistently at 100%
- RAM bars all red/filled
- Swap constantly increasing
- High load average (top right)

**Press `q` to quit htop**

---

### Check Disk Space

**Command:**

```bash
df -h
```

**Red flags:**

- ⚠️ Root volume `/dev/root` at 100%
- ⚠️ `/var/lib/docker` approaching capacity

**Clean up if needed:**

```bash
docker system prune -a --volumes
```

---

## Step 2: Check Container Status

### List All Containers

**Command:**

```bash
docker ps -a
```

**Understanding container states:**

| State | Meaning | Action |
|-------|---------|--------|
| `Up` | ✅ Running normally | Good |
| `Up (unhealthy)` | ⚠️ Healthcheck failing | Check logs, may still work |
| `Restarting` | 🔴 Crash loop | Check logs immediately |
| `Exited (0)` | ℹ️ Clean shutdown | Intentional stop |
| `Exited (1)` | 🔴 Application error | Check logs for errors |
| `Exited (137)` | 🔴 **OOM Killed** | Memory exhausted |

**Most critical:** `Exited (137)` = kernel killed the process due to out of memory

---

### Check Specific Container

**Command:**

```bash
docker inspect smarthire-backend | grep -A 10 State
```

**Look for:**

```json
"State": {
    "Status": "exited",
    "ExitCode": 137,
    "OOMKilled": true
}
```

`"OOMKilled": true` confirms memory was the issue.

---

## Step 3: Inspect Container Logs

### Backend Logs

**Command:**

```bash
# Last 200 lines
docker logs smarthire-backend --tail=200

# Real-time (follow)
docker logs smarthire-backend -f

# With timestamps
docker logs smarthire-backend --timestamps --tail=200
```

**What to look for:**

**Signs of OOM kill:**

```
[startup messages]
[normal operations]
Killed
```

Sudden "Killed" without stack trace = OOM

**Application errors:**

```
Traceback (most recent call last):
  File...
  Error: ...
```

These are code bugs, not resource issues

**Database issues:**

```
connection refused
timeout
```

PostgreSQL container might be down

---

### Frontend Logs

**Command:**

```bash
docker logs smarthire-frontend --tail=100
```

**What to expect:**

```
✅ nginx: [notice] start worker process
✅ nginx: [notice] start worker process
```

**Problems:**

```
❌ nginx: [emerg] bind() to 0.0.0.0:80 failed
❌ nginx: [error] open() "/etc/nginx/..." failed
```

---

### PostgreSQL Logs

**Command:**

```bash
docker logs smarthire-postgres --tail=100
```

**Healthy output:**

```
✅ database system is ready to accept connections
```

**Problems:**

```
❌ database system was not properly shut down
❌ could not create shared memory segment
```

---

## Step 4: Check Kernel Logs (OOM Detection)

### View Recent Kernel Messages

**Command:**

```bash
dmesg | tail -50
```

**Or search for OOM events:**

```bash
dmesg | grep -i "killed process"
```

**Confirmed OOM example:**

```
Out of memory: Kill process 1234 (python) score 850 or sacrifice child
Killed process 1234 (python) total-vm:890432kB
```

**What this means:**

- ✅ Confirms OOM kill
- ❌ This is NOT an application bug
- ❌ This is a resource exhaustion issue
- ✅ Fix: Add swap, reduce memory usage, or upgrade instance

---

## Step 5: Check Docker Compose Configuration

### Common Issue: `deploy:` Block Ignored

**In `docker-compose.yml`:**

```yaml
services:
  backend:
    deploy:
      resources:
        limits:
          memory: 512M  # ❌ IGNORED if not using Swarm!
```

**Why ignored:**

- `deploy:` only works in **Docker Swarm mode**
- Most setups use **Docker Compose** (standalone)

### Use Compose-Native Limits Instead

**Correct approach:**

```yaml
services:
  backend:
    image: your-image
    mem_limit: 512m        # ✅ Works in Compose
    memswap_limit: 1024m   # ✅ mem + swap limit
    cpus: "1.0"            # ✅ CPU limit
```

**Apply changes:**

```bash
docker-compose -f docker-compose.ec2.yml down
docker-compose -f docker-compose.ec2.yml up -d
```

---

## Step 6: Verify Service Availability

### Check Open Ports

**Command:**

```bash
ss -tulpn | grep LISTEN
```

**Expected output:**

```
tcp   LISTEN   0   511   0.0.0.0:80        # nginx (frontend)
tcp   LISTEN   0   511   0.0.0.0:443       # nginx (https)
tcp   LISTEN   0   511   127.0.0.1:8000    # backend
tcp   LISTEN   0   511   127.0.0.1:5432    # postgres
```

**Problems:**

- Backend not on 8000 → Container not running
- Nothing on 80/443 → Nginx not running

---

### Test Backend Directly

**Command:**

```bash
curl http://localhost:8000/health
```

**Expected:**

```json
{"status":"healthy","timestamp":"2026-02-19T..."}
```

**If fails:**

```bash
# Check if backend container is running
docker ps | grep backend

# Check backend logs
docker logs smarthire-backend --tail=50
```

---

### Test Frontend

**Command:**

```bash
curl http://localhost:80
```

**Should return HTML content.**

**If fails:**

```bash
docker ps | grep frontend
docker logs smarthire-frontend
```

---

## Step 7: Clean Restart Procedure

### Complete System Restart

**Commands:**

```bash
# Stop all containers
docker-compose -f docker-compose.ec2.yml down

# Optional: Clean up resources
docker system prune -f

# Restart Docker daemon
sudo systemctl restart docker

# Verify Docker is running
sudo systemctl status docker

# Start containers
docker-compose -f docker-compose.ec2.yml up -d

# Check status
docker-compose -f docker-compose.ec2.yml ps
```

---

# Common Issues & Solutions

## Issue 1: Container Exits with Code 137 (OOM)

### Symptoms

- Container randomly exits
- `docker ps -a` shows `Exited (137)`
- `docker inspect` shows `"OOMKilled": true`
- `dmesg` shows "Killed process"

### Root Cause

Linux kernel killed the process due to memory exhaustion.

### Solutions

#### Solution A: Add Swap Memory (REQUIRED for t2.micro)

**Create 2GB swap file:**

```bash
# Create swap file
sudo fallocate -l 2G /swapfile

# Set permissions
sudo chmod 600 /swapfile

# Format as swap
sudo mkswap /swapfile

# Enable swap
sudo swapon /swapfile

# Verify
free -h
# Should show Swap: 2.0Gi
```

**Make permanent (survives reboot):**

```bash
echo '/swapfile none swap sw 0 0' | sudo tee -a /etc/fstab
```

**Verify it persists:**

```bash
cat /etc/fstab | grep swapfile
```

---

#### Solution B: Reduce Backend Workers

**Problem:** Multiple workers multiply memory usage

**Check current worker count:**

```bash
docker exec smarthire-backend ps aux | grep uvicorn
```

**In your Dockerfile or start command:**

```dockerfile
# ❌ Bad for t2.micro
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--workers", "4"]

# ✅ Good for t2.micro
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--workers", "1"]
```

**Or in docker-compose:**

```yaml
backend:
  command: uvicorn app.main:app --host 0.0.0.0 --workers 1
```

---

#### Solution C: Set Memory Limits

**Add to docker-compose.ec2.yml:**

```yaml
services:
  backend:
    mem_limit: 512m
    memswap_limit: 768m
  
  frontend:
    mem_limit: 256m
  
  postgres:
    mem_limit: 256m
```

**This prevents one container from consuming all RAM.**

---

#### Solution D: Upgrade EC2 Instance

| Instance | RAM | Status | Monthly Cost (after free tier) |
|----------|-----|--------|-------------------------------|
| t2.micro | 1 GB | ❌ Fragile | ~$8.50 |
| t3.small | 2 GB | ✅ Minimum | ~$15 |
| t3.medium | 4 GB | ⭐ Comfortable | ~$30 |

**Upgrade process:**

1. AWS Console → EC2 → Select instance
2. Actions → Instance Settings → Change instance type
3. Select t3.small (2 GB RAM)
4. Start instance

---

## Issue 2: Healthcheck Failures (Container Shows "Unhealthy")

### Symptoms

- Container status: `Up (unhealthy)`
- Application actually works fine in browser
- No errors in logs

### Understanding Healthchecks

**In Dockerfile:**

```dockerfile
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD python -c "import requests; requests.get('http://localhost:8000/health')" || exit 1
```

**Common issues:**

- ❌ Healthcheck command requires packages not in image
- ❌ Healthcheck URL incorrect
- ❌ Timeout too short for slow startup
- ❌ Start period too short

### Solutions

#### Solution A: Fix Healthcheck

**Better healthcheck (doesn't need external packages):**

```dockerfile
HEALTHCHECK --interval=30s --timeout=10s --start-period=30s --retries=3 \
    CMD curl -f http://localhost:8000/health || exit 1
```

Make sure `curl` is in your Docker image:

```dockerfile
RUN apt-get update && apt-get install -y curl
```

---

#### Solution B: Increase Start Period

**If service is slow to start:**

```dockerfile
HEALTHCHECK --start-period=60s ...
```

---

#### Solution C: Disable Healthcheck (Temporary)

**In docker-compose.ec2.yml:**

```yaml
services:
  backend:
    healthcheck:
      disable: true
```

**Only use this if:**

- Healthcheck is misconfigured
- Service works but shows unhealthy
- You're debugging

---

## Issue 3: Build Fails - "No Space Left on Device"

### Symptoms

- `docker build` fails
- Error: "no space left on device"
- Can't create files

### Check Disk Usage

```bash
df -h
docker system df
```

### Solutions

#### Solution A: Clean Docker Cache

```bash
# Remove unused images, containers, networks
docker system prune -a --volumes

# Type 'y' to confirm
```

**This removes:**

- Stopped containers
- Unused images
- Unused networks
- Build cache
- Unused volumes

---

#### Solution B: Remove Specific Items

**Remove old images:**

```bash
docker image prune -a
```

**Remove volumes:**

```bash
docker volume prune
```

**Remove build cache:**

```bash
docker builder prune -a
```

---

## Issue 4: EC2 Instance Freezes / SSH Hangs

### Symptoms

- Can't SSH into instance
- Instance Status Checks show warnings
- Console (via AWS web) is unresponsive

### Root Cause

Kernel panic or complete memory exhaustion with no swap.

### Solutions

#### Solution A: Reboot via AWS Console

1. AWS Console → EC2 → Instances
2. Select your instance
3. Instance state → Reboot
4. Wait 2-3 minutes

---

#### Solution B: Add Swap (After Reboot)

```bash
# After reboot, SSH in and immediately add swap
sudo fallocate -l 2G /swapfile
sudo chmod 600 /swapfile
sudo mkswap /swapfile
sudo swapon /swapfile
echo '/swapfile none swap sw 0 0' | sudo tee -a /etc/fstab
```

---

#### Solution C: Prevent Future Freezes

**Add monitoring script:**

```bash
cat > ~/check-memory.sh << 'EOF'
#!/bin/bash
AVAILABLE=$(free -m | awk 'NR==2{print $7}')
if [ $AVAILABLE -lt 100 ]; then
    echo "$(date): Low memory - $AVAILABLE MB" >> ~/memory-alerts.log
    # Restart services if critically low
    if [ $AVAILABLE -lt 50 ]; then
        docker-compose -f /home/ubuntu/smarthire/docker-compose.ec2.yml restart
    fi
fi
EOF

chmod +x ~/check-memory.sh

# Run every 5 minutes
crontab -e
# Add: */5 * * * * ~/check-memory.sh
```

---

## Issue 5: Database Connection Errors

### Symptoms

- Backend logs: "connection refused"
- Backend logs: "timeout"
- API returns 500 errors

### Check PostgreSQL Status

```bash
docker ps | grep postgres
docker logs smarthire-postgres --tail=50
```

### Solutions

#### Solution A: Restart PostgreSQL

```bash
docker-compose -f docker-compose.ec2.yml restart postgres
```

---

#### Solution B: Check Database URL

**In .env file:**

```bash
cat .env | grep DATABASE_URL
```

**Should be:**

```env
# For docker-compose (containers talk via service names)
DATABASE_URL=postgresql+asyncpg://smarthire:password@postgres:5432/smarthire_db

# NOT this (localhost won't work from inside containers):
# DATABASE_URL=postgresql+asyncpg://smarthire:password@localhost:5432/smarthire_db
```

---

#### Solution C: Check Network

```bash
docker network ls
docker network inspect smarthire-network
```

All containers should be on the same network.

---

# Recommended Configuration

## Minimum EC2 Setup for Stability

### T2.micro (1 GB RAM) - With Swap

```yaml
# docker-compose.ec2.yml
services:
  postgres:
    mem_limit: 256m
  
  backend:
    mem_limit: 512m
    command: uvicorn app.main:app --host 0.0.0.0 --workers 1
  
  frontend:
    mem_limit: 256m
```

**Plus 2GB swap file REQUIRED**

---

### T3.small (2 GB RAM) - Comfortable

```yaml
# docker-compose.ec2.yml
services:
  postgres:
    mem_limit: 512m
  
  backend:
    mem_limit: 1024m
    command: uvicorn app.main:app --host 0.0.0.0 --workers 2
  
  frontend:
    mem_limit: 512m
```

**Swap recommended but not critical**

---

## Monitoring Commands

### Quick Health Check Script

```bash
cat > ~/health-check.sh << 'EOF'
#!/bin/bash
echo "=== Memory ==="
free -h

echo -e "\n=== Disk ==="
df -h | grep -E "(Filesystem|/dev/root)"

echo -e "\n=== Docker Containers ==="
docker ps --format "table {{.Names}}\t{{.Status}}"

echo -e "\n=== Ports ==="
ss -tulpn | grep LISTEN

echo -e "\n=== Recent OOM Events ==="
dmesg | grep -i "killed process" | tail -5
EOF

chmod +x ~/health-check.sh
```

**Run with:**

```bash
~/health-check.sh
```

---

# Mental Model for Debugging

## Decision Tree

```
Container exited?
├─ Exit code 137? → OOM (add swap, reduce memory, upgrade)
├─ Exit code 1? → Application error (check logs)
└─ Status "Restarting"? → Crash loop (check logs)

EC2 unresponsive?
├─ SSH hangs? → Memory exhausted (reboot, add swap)
└─ High CPU? → Check docker stats

Healthcheck failing but works in browser?
├─ Healthcheck misconfigured → Fix or disable
└─ Slow startup → Increase start-period

API errors?
├─ 500 errors? → Check backend logs
├─ Connection refused? → Check database
└─ CORS errors? → Check CORS_ORIGINS in .env
```

---

# Quick Reference

## Essential Commands

```bash
# System health
free -h                    # Memory
df -h                      # Disk
htop                       # Real-time resources
dmesg | tail -50          # Kernel logs

# Docker status
docker ps -a              # All containers
docker logs <container>   # Container logs
docker stats              # Resource usage

# Restart
docker-compose -f docker-compose.ec2.yml restart
docker-compose -f docker-compose.ec2.yml down && \
docker-compose -f docker-compose.ec2.yml up -d

# Clean up
docker system prune -a --volumes

# Swap
sudo swapon -s            # Check swap
free -h                   # Verify swap
```

---

## Exit Codes Reference

| Code | Meaning | Common Cause |
|------|---------|--------------|
| 0 | Clean exit | Intentional stop |
| 1 | Application error | Bug in code |
| 137 | SIGKILL (OOM) | Out of memory |
| 139 | Segmentation fault | Memory corruption |
| 143 | SIGTERM | Docker stop |

---

**Keep this guide handy — it covers 95% of issues you'll encounter with SmartHire on small EC2 instances!** 🛠️
