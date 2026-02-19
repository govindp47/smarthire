# Deployment Guide: Vercel (Frontend) + DuckDNS (Backend)

## SmartHire — Free Production Setup with HTTPS

> **Cost:** $0/month forever  
> **Result:** Frontend on global CDN, Backend with free SSL  
> **Time:** ~45 minutes

---

## Overview

### Current State → Target State

**Before (Everything on EC2):**

```
EC2 Instance (http://YOUR-EC2-IP)
├── Frontend (React) - Port 80
├── Backend (FastAPI) - Port 8000  
└── PostgreSQL - Port 5432
```

**After (Separated & Secured):**

```
Vercel CDN                          EC2 Instance
Frontend (React)              Backend (FastAPI + PostgreSQL)
https://yourapp.vercel.app → https://smarthire.duckdns.org
     ↓ API calls                    ↓
     └──────────────────────────────┘
```

### Benefits

- ✅ Frontend on global CDN (faster for users worldwide)
- ✅ Auto-deploy from GitHub (push to deploy)
- ✅ Free HTTPS for both frontend and backend
- ✅ Professional developer setup
- ✅ 100% free

---

## Prerequisites

- ✅ EC2 instance running with Docker
- ✅ SmartHire code on GitHub
- ✅ Both frontend and backend currently running on EC2
- ✅ GitHub account
- ✅ Email address (for SSL certificate)

---

# Phase 1: Setup DuckDNS (Free Domain for Backend)

## Step 1: Create DuckDNS Account

1. Go to <https://www.duckdns.org>
2. Click **Sign in** → Choose **GitHub** (recommended)
3. After login, you'll see the dashboard

## Step 2: Create Subdomain

1. In the **subdomains** section, enter your desired name:

   ```
   smarthire  (or smarthire-yourname if taken)
   ```

2. Click **add domain**
3. **Copy your token** (shown on page — looks like `12345678-1234-1234-1234-123456789abc`)

**Save these credentials:**

```
Domain: smarthire.duckdns.org
Token:  12345678-1234-1234-1234-123456789abc
```

## Step 3: Point DuckDNS to Your EC2 IP

**On DuckDNS website:**

1. Find your subdomain in the list
2. In the **current ip** box, enter your **EC2 Public IP address**
3. Click **update ip**
4. Should show: "OK" or green checkmark

## Step 4: Verify DNS Resolution

**Wait 1-2 minutes, then test on your computer:**

```bash
# Test DNS resolution
nslookup smarthire.duckdns.org

# Expected output should show your EC2 IP
```

**Test in browser:**

```
http://smarthire.duckdns.org:8000/docs
```

Should display your FastAPI Swagger documentation.

## Step 5: Setup Auto-Update (Recommended)

This keeps DuckDNS updated if your EC2 IP changes.

**SSH into EC2:**

```bash
ssh -i ~/.ssh/smarthire-key.pem ubuntu@YOUR-EC2-IP
```

**Create update script:**

```bash
nano ~/update-duckdns.sh
```

**Paste this (replace `smarthire` and token with your values):**

```bash
#!/bin/bash
echo url="https://www.duckdns.org/update?domains=smarthire&token=YOUR-ACTUAL-TOKEN&ip=" | curl -k -o ~/duckdns.log -K -
```

**Make executable and test:**

```bash
chmod +x ~/update-duckdns.sh
~/update-duckdns.sh

# Verify it worked
cat ~/duckdns.log
# Should say: OK
```

**Setup cron job (runs every 5 minutes):**

```bash
crontab -e
# Choose nano if asked (option 1)

# Add this line at the bottom:
*/5 * * * * ~/update-duckdns.sh >/dev/null 2>&1

# Save and exit: Ctrl+X, Y, Enter
```

**✅ Phase 1 Complete!** Backend now has domain: `smarthire.duckdns.org`

---

# Phase 2: Deploy Frontend to Vercel

## Step 1: Prepare Frontend Configuration

**On your local machine:**

```bash
cd smarthire/frontend
```

### Create `vercel.json`

```bash
cat > vercel.json << 'EOF'
{
  "buildCommand": "npm run build",
  "outputDirectory": "dist",
  "devCommand": "npm run dev",
  "rewrites": [
    {
      "source": "/api/:path*",
      "destination": "http://smarthire.duckdns.org:8000/api/:path*"
    },
    {
      "source": "/(.*)",
      "destination": "/index.html"
    }
  ]
}
EOF
```

## Step 2: Commit and Push

```bash
cd ..  # Back to smarthire root

git add frontend/vercel.json
git commit -m "Add Vercel configuration for frontend deployment"
git push origin main
```

## Step 3: Create Vercel Account

1. Go to <https://vercel.com/signup>
2. Click **Continue with GitHub**
3. Authorize Vercel to access your repositories

## Step 4: Import Project to Vercel

1. After login, click **Add New** → **Project**
2. **Import Git Repository:**
   - Find `smarthire` in the list
   - Click **Import**

## Step 5: Configure Project

**Framework Preset:**

- Select: **Vite** (should auto-detect)

**Root Directory:**

- Click **Edit**
- Enter: `frontend`
- Click **Continue**

**Build Settings** (should auto-fill):

- Build Command: `npm run build`
- Output Directory: `dist`
- Install Command: `npm install`

**Environment Variables:**

- Should auto-detect from `.env.production`
- If not, click **Add** and enter:

  ```
  Name:  VITE_API_BASE_URL
  Value: http://smarthire.duckdns.org:8000
  ```

Click **Deploy** and wait 1-3 minutes.

## Step 6: Get Your Vercel URL

After deployment succeeds:

1. You'll see: **🎉 Congratulations!**
2. Your URL will be something like: `smarthire-abc123xyz.vercel.app`
3. Click **Visit** to see your site

**Save this URL:**

```
Vercel URL: https://smarthire-abc123xyz.vercel.app
```

## Step 7: Test Frontend (Expected Partial Failure)

Visit: `https://smarthire-abc123xyz.vercel.app`

**Expected behavior:**

- ✅ Page loads correctly
- ⚠️ API calls fail with CORS or mixed content errors

**Why it fails:**

- Frontend is HTTPS (`https://yourapp.vercel.app`)
- Backend is HTTP (`http://smarthire.duckdns.org:8000`)
- Browsers block HTTPS → HTTP requests (mixed content)

**Fix:** Add HTTPS to backend (next phase)

## Step 8: Update Backend CORS

**SSH into EC2:**

```bash
ssh -i ~/.ssh/smarthire-key.pem ubuntu@YOUR-EC2-IP
cd /home/ubuntu/smarthire
```

**Edit `.env`:**

```bash
nano .env
```

**Update `CORS_ORIGINS` line (replace with your actual Vercel URL):**

```env
# Before:
CORS_ORIGINS=http://YOUR-EC2-IP

# After:
CORS_ORIGINS=https://smarthire-abc123xyz.vercel.app,http://localhost:3000
```

**Save:** `Ctrl+X`, `Y`, `Enter`

**Restart backend:**

```bash
docker-compose -f docker-compose.ec2.yml restart backend
```

**✅ Phase 2 Complete!** Frontend is on Vercel (but can't communicate with backend yet).

---

# Phase 3: Add HTTPS to Backend (Let's Encrypt)

## The Problem

```
HTTPS Frontend → HTTP Backend = ❌ Blocked by browser
```

## The Solution

```
HTTPS Frontend → HTTPS Backend = ✅ Works perfectly
```

## Step 1: Install Nginx and Certbot

**SSH into EC2:**

```bash
ssh -i ~/.ssh/smarthire-key.pem ubuntu@YOUR-EC2-IP
```

**Install packages:**

```bash
sudo apt update
sudo apt install nginx certbot python3-certbot-nginx -y
```

## Step 2: Configure Nginx as Reverse Proxy

**Create Nginx configuration:**

```bash
sudo nano /etc/nginx/sites-available/smarthire
```

**Paste this configuration:**

```nginx
# HTTP server - will redirect to HTTPS after cert is obtained
server {
    listen 80;
    server_name smarthire.duckdns.org;

    # Let's Encrypt validation path
    location /.well-known/acme-challenge/ {
        root /var/www/html;
    }

    # Proxy all other requests to backend
    location / {
        proxy_pass http://localhost:8000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }
}
```

**Save:** `Ctrl+X`, `Y`, `Enter`

**Enable the site:**

```bash
# Create symbolic link
sudo ln -s /etc/nginx/sites-available/smarthire /etc/nginx/sites-enabled/

# Remove default site
sudo rm /etc/nginx/sites-enabled/default

# Test configuration
sudo nginx -t
# Should say: "syntax is okay" and "test is successful"

# Start Nginx
sudo systemctl restart nginx
sudo systemctl enable nginx
```

**Test:**

```bash
# Should work without :8000 port now
curl http://smarthire.duckdns.org
```

## Step 3: Obtain SSL Certificate

**Run Certbot:**

```bash
sudo certbot --nginx -d smarthire.duckdns.org
```

**Follow the prompts:**

```
Email address: your@email.com
Agree to Terms of Service: Y
Share email with EFF: N (your choice)
```

**When asked about redirect:**

```
Please choose whether or not to redirect HTTP traffic to HTTPS:
1: No redirect
2: Redirect ← Choose this option
```

**What Certbot does:**

1. ✅ Verifies you own the domain
2. ✅ Obtains SSL certificate from Let's Encrypt
3. ✅ Automatically updates Nginx config to use HTTPS
4. ✅ Sets up auto-renewal (runs twice daily)

## Step 4: Verify HTTPS Works

**Test in browser:**

```
https://smarthire.duckdns.org
```

Should show:

- ✅ 🔒 Lock icon in address bar
- ✅ Valid SSL certificate
- ✅ Your API response

**Test API documentation:**

```
https://smarthire.duckdns.org/docs
```

Should display Swagger UI with HTTPS.

## Step 5: Verify Auto-Renewal

**Test certificate renewal (dry run):**

```bash
sudo certbot renew --dry-run
```

Should say: "Congratulations, all simulated renewals succeeded"

**✅ Phase 3 Complete!** Backend now has HTTPS with auto-renewing SSL certificate.

---

# Phase 4: Connect Frontend to Secured Backend

## Step 1: Update Frontend Environment Variable

### Option A: Via Vercel Dashboard

1. Go to <https://vercel.com>
2. Select your `smarthire` project
3. Go to **Settings** → **Environment Variables**
4. Find `VITE_API_BASE_URL`
5. Click **Edit**
6. Change value to:

   ```
   https://smarthire.duckdns.org
   ```

   (Note: No `:8000` port, HTTPS not HTTP)
7. Click **Save**
8. Go to **Deployments** tab
9. Click latest deployment → **Redeploy** button

### Option B: Via Local Update

```bash
# On your local machine
cd smarthire/frontend

# Update .env.production
cat > .env.production << 'EOF'
VITE_API_BASE_URL=https://smarthire.duckdns.org
EOF

# Commit and push
git add .env.production
git commit -m "Update API URL to use HTTPS"
git push origin main
```

Vercel auto-deploys on push to main. Wait 1-2 minutes.

## Step 2: Update Backend CORS (Final)

**SSH into EC2:**

```bash
ssh -i ~/.ssh/smarthire-key.pem ubuntu@YOUR-EC2-IP
cd /home/ubuntu/smarthire
```

**Edit `.env`:**

```bash
nano .env
```

**Update to use HTTPS URL:**

```env
CORS_ORIGINS=https://smarthire-abc123xyz.vercel.app,https://smarthire.duckdns.org
```

**Restart backend:**

```bash
docker-compose -f docker-compose.ec2.yml restart backend
```

## Step 3: Complete End-to-End Test

**Visit your Vercel frontend:**

```
https://smarthire-abc123xyz.vercel.app
```

**Test all functionality:**

1. ✅ Sign up for new account
2. ✅ Login
3. ✅ Create a job posting
4. ✅ Upload a resume
5. ✅ View candidates
6. ✅ Use AI query feature

**Everything should work perfectly!** 🎉

**✅ Phase 4 Complete!** Frontend and backend are fully connected over HTTPS.

---

# Phase 5: Cleanup (Optional)

Since frontend is now on Vercel, the frontend container on EC2 is no longer needed.

## Option A: Stop Frontend Container (Recommended)

**SSH into EC2:**

```bash
ssh -i ~/.ssh/smarthire-key.pem ubuntu@YOUR-EC2-IP
cd /home/ubuntu/smarthire
```

**Stop and remove frontend container:**

```bash
docker stop smarthire-frontend
docker rm smarthire-frontend
```

**Backend and PostgreSQL continue running normally.**

## Option B: Keep Everything (No Action Needed)

Leave frontend container running as a backup. It doesn't use much resources.

---

# Final Architecture

```
┌─────────────────────────────────┐
│     Vercel (Global CDN)         │
│   Frontend (React + Vite)       │
│                                 │
│  https://yourapp.vercel.app     │ ← Users visit here
└────────────┬────────────────────┘
             │ HTTPS API calls
             ↓
┌─────────────────────────────────┐
│   EC2 Instance (t2.micro)       │
│  ┌────────────────────────────┐ │
│  │  Nginx (Port 443)          │ │ ← SSL termination
│  │  - HTTPS listener          │ │
│  │  - Let's Encrypt cert      │ │
│  └──────────┬─────────────────┘ │
│             ↓                   │
│  ┌────────────────────────────┐ │
│  │  Backend (Port 8000)       │ │
│  │  - FastAPI                 │ │
│  │  - Python 3.11             │ │
│  └────────────────────────────┘ │
│  ┌────────────────────────────┐ │
│  │  PostgreSQL (Port 5432)    │ │
│  │  - Resume data             │ │
│  └────────────────────────────┘ │
│                                 │
│  smarthire.duckdns.org          │ ← Backend domain
└─────────────────────────────────┘
```

---

# Access Points

| Service | URL | Purpose |
|---------|-----|---------|
| **Frontend** | `https://yourapp.vercel.app` | Main user interface (React) |
| **Backend API** | `https://smarthire.duckdns.org` | API endpoints (called by frontend) |
| **API Docs** | `https://smarthire.duckdns.org/docs` | Swagger/OpenAPI documentation |

---

# Cost Breakdown

| Service | Monthly Cost |
|---------|--------------|
| Vercel (Frontend) | $0.00 |
| DuckDNS (Domain) | $0.00 |
| Let's Encrypt (SSL) | $0.00 |
| EC2 t2.micro | $0.00 (free tier) |
| **Total** | **$0.00** |

**After free tier expires (12 months):**

- EC2 t2.micro: ~$8-10/month
- Everything else: Still $0

---

# Auto-Deployment & Maintenance

## Frontend Auto-Deploy (Vercel)

**How it works:**

```
Local → git push origin main → GitHub → Vercel auto-deploys
```

**Triggers deployment:**

- ✅ Push to `main` branch
- ✅ Merge PR to `main`
- ✅ Changes in `frontend/` directory only

**Does NOT trigger deployment:**

- ❌ Push to other branches (creates preview instead)
- ❌ Changes to `backend/` directory
- ❌ Changes to `docs/` or `README.md`

**Deployment time:** 1-3 minutes

**Example workflow:**

```bash
# Make frontend changes
cd smarthire/frontend
nano src/pages/Dashboard.jsx

# Commit and push
cd ..
git add frontend/
git commit -m "Update dashboard UI"
git push origin main

# ✅ Vercel automatically builds and deploys
# ✅ Live in ~2 minutes at https://yourapp.vercel.app
```

## Backend Manual Deploy (EC2)

Backend does NOT auto-deploy. Manual process:

```bash
# On local machine
git push origin main

# Then on EC2
ssh -i ~/.ssh/smarthire-key.pem ubuntu@YOUR-EC2-IP
cd /home/ubuntu/smarthire
git pull
docker-compose -f docker-compose.ec2.yml restart backend
```

## SSL Certificate Auto-Renewal

**Certbot automatically renews certificates:**

- Runs twice daily via cron
- Renews when cert has <30 days left
- No manual intervention needed

**Verify auto-renewal:**

```bash
sudo certbot renew --dry-run
```

## DuckDNS Auto-Update

**Cron job updates IP every 5 minutes:**

- Automatically configured in Phase 1
- Runs even if IP doesn't change (harmless)
- Check logs: `cat ~/duckdns.log`

---

# Troubleshooting

## Issue 1: API Calls Fail (CORS Error)

**Symptom:** Frontend loads but API returns CORS error

**Check:**

```bash
# On EC2
cd /home/ubuntu/smarthire
cat .env | grep CORS_ORIGINS
```

**Should include your Vercel URL:**

```env
CORS_ORIGINS=https://your-actual-vercel-url.vercel.app
```

**Fix:**

```bash
nano .env
# Update CORS_ORIGINS with correct Vercel URL
docker-compose -f docker-compose.ec2.yml restart backend
```

---

## Issue 2: Mixed Content Error

**Symptom:** "Mixed Content: The page was loaded over HTTPS, but requested an insecure resource"

**Cause:** Frontend using HTTP backend URL instead of HTTPS

**Fix:**

1. Vercel Dashboard → Settings → Environment Variables
2. Verify `VITE_API_BASE_URL` uses `https://` not `http://`
3. Redeploy frontend

---

## Issue 3: SSL Certificate Errors

**Symptom:** Browser shows "Your connection is not private"

**Check certificate:**

```bash
sudo certbot certificates
```

**Renew manually if needed:**

```bash
sudo certbot renew --force-renewal
sudo systemctl restart nginx
```

---

## Issue 4: DuckDNS Not Resolving

**Test DNS:**

```bash
nslookup smarthire.duckdns.org
```

**If fails, update manually:**

```bash
# On EC2
~/update-duckdns.sh
cat ~/duckdns.log
# Should say: OK
```

**If still fails:**

- Check token is correct in `~/update-duckdns.sh`
- Verify IP is correct on DuckDNS website
- Wait 5 minutes for DNS propagation

---

## Issue 5: Nginx Not Starting

**Check status:**

```bash
sudo systemctl status nginx
```

**View error logs:**

```bash
sudo tail -f /var/log/nginx/error.log
```

**Test configuration:**

```bash
sudo nginx -t
```

**Restart:**

```bash
sudo systemctl restart nginx
```

---

## Issue 6: Port 80 or 443 Already in Use

**Check what's using ports:**

```bash
sudo lsof -i :80
sudo lsof -i :443
```

**If Docker frontend container is using port 80:**

```bash
docker stop smarthire-frontend
docker rm smarthire-frontend
sudo systemctl restart nginx
```

---

# Verification Checklist

After completing all phases, verify:

- [ ] DuckDNS resolves to EC2 IP: `nslookup smarthire.duckdns.org`
- [ ] Backend HTTPS works: `https://smarthire.duckdns.org/docs`
- [ ] SSL certificate is valid (🔒 icon in browser)
- [ ] Frontend loads: `https://yourapp.vercel.app`
- [ ] Can create account on frontend
- [ ] Can login
- [ ] Can create job posting
- [ ] Can upload resume
- [ ] API calls work (check browser DevTools Network tab)
- [ ] No CORS errors
- [ ] No mixed content errors

---

# Monitoring & Logs

## View Frontend Logs (Vercel)

1. Vercel Dashboard → Your project
2. **Deployments** tab
3. Click a deployment
4. View **Build Logs** and **Function Logs**

## View Backend Logs (EC2)

```bash
# Real-time logs
docker-compose -f docker-compose.ec2.yml logs -f backend

# Last 100 lines
docker-compose -f docker-compose.ec2.yml logs --tail=100 backend

# Nginx logs
sudo tail -f /var/log/nginx/access.log
sudo tail -f /var/log/nginx/error.log
```

---

# Next Steps (Optional Enhancements)

1. **Custom Vercel Domain:**
   - Settings → Domains → Add `yourapp.vercel.app`

2. **GitHub Actions:**
   - Auto-deploy backend on push
   - Run tests before deploy

3. **Monitoring:**
   - Add Vercel Analytics
   - Setup error tracking (Sentry)

4. **Performance:**
   - Enable Vercel Edge Functions
   - Add caching headers

5. **Security:**
   - Rate limiting on backend
   - Add API authentication
   - Setup firewall rules

---

# Quick Reference Commands

## Deploy Frontend

```bash
git push origin main  # Vercel auto-deploys
```

## Update Backend

```bash
# On EC2
cd /home/ubuntu/smarthire
git pull
docker-compose -f docker-compose.ec2.yml restart backend
```

## Check SSL Certificate

```bash
sudo certbot certificates
```

## Update DuckDNS Manually

```bash
~/update-duckdns.sh
cat ~/duckdns.log
```

## Restart Nginx

```bash
sudo systemctl restart nginx
```

## View Logs

```bash
# Backend
docker-compose -f docker-compose.ec2.yml logs -f backend

# Nginx
sudo tail -f /var/log/nginx/error.log
```

---

# Support

If you encounter issues:

1. Check the troubleshooting section above
2. View relevant logs
3. Verify all URLs are using HTTPS (not HTTP)
4. Ensure CORS_ORIGINS includes your Vercel URL
5. Test DNS resolution with `nslookup`

---

**Deployment Complete!** 🎉

You now have a professional, production-ready setup with:

- ✅ Frontend on global CDN with auto-deploy
- ✅ Backend with free HTTPS and auto-renewing SSL
- ✅ Free custom domain for backend
- ✅ Zero monthly cost
- ✅ Industry-standard architecture
