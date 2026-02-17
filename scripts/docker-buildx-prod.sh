#!/bin/bash
# SmartHire - Build and Push to Docker Hub (Cross-Platform)
# Run this on your LOCAL Mac machine (builds for Linux EC2)

set -e  # Exit on error

# Colors for output
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

echo -e "${GREEN}🚀 SmartHire - Docker Hub Build & Push${NC}"
echo -e "${BLUE}Cross-platform build: Mac → Linux (EC2 compatible)${NC}"
echo -e "${BLUE}Target platform: linux/amd64${NC}"
echo ""

# Get Docker Hub username
read -p "Enter your Docker Hub username: " DOCKER_USERNAME

if [ -z "$DOCKER_USERNAME" ]; then
    echo -e "${RED}❌ Docker Hub username is required!${NC}"
    exit 1
fi

echo ""
echo -e "${YELLOW}📋 Summary:${NC}"
echo "  Backend image:  $DOCKER_USERNAME/smarthire-backend:latest"
echo "  Frontend image: $DOCKER_USERNAME/smarthire-frontend:latest"
echo "  Build method:   docker buildx (linux/amd64 for EC2)"
echo ""
read -p "Continue? (y/n) " -n 1 -r
echo
if [[ ! $REPLY =~ ^[Yy]$ ]]; then
    echo "Cancelled."
    exit 1
fi

# Login to Docker Hub
echo ""
echo -e "${GREEN}🔐 Logging into Docker Hub...${NC}"
docker login
if [ $? -ne 0 ]; then
    echo -e "${RED}❌ Docker login failed!${NC}"
    exit 1
fi

# Setup buildx for cross-platform
echo ""
echo -e "${GREEN}🔧 Setting up cross-platform builder...${NC}"

if docker buildx ls | grep -q "smarthire-builder"; then
    echo "Builder already exists, using it."
    docker buildx use smarthire-builder
else
    echo "Creating new builder..."
    docker buildx create --name smarthire-builder --use
fi

docker buildx inspect --bootstrap
echo -e "${GREEN}✅ Builder ready!${NC}"

# Build and push backend (linux/amd64)
echo ""
echo -e "${GREEN}🏗️  Building & pushing backend (linux/amd64)...${NC}"
echo -e "${BLUE}Builds directly for EC2's architecture - no compatibility issues!${NC}"

docker buildx build \
    --platform linux/amd64 \
    --tag $DOCKER_USERNAME/smarthire-backend:latest \
    --push \
    ./backend

if [ $? -ne 0 ]; then
    echo -e "${RED}❌ Backend build/push failed!${NC}"
    exit 1
fi
echo -e "${GREEN}✅ Backend done!${NC}"

# Build and push frontend (linux/amd64)
echo ""
echo -e "${GREEN}🎨 Building & pushing frontend (linux/amd64)...${NC}"

docker buildx build \
    --platform linux/amd64 \
    --tag $DOCKER_USERNAME/smarthire-frontend:latest \
    --push \
    ./frontend

if [ $? -ne 0 ]; then
    echo -e "${RED}❌ Frontend build/push failed!${NC}"
    exit 1
fi
echo -e "${GREEN}✅ Frontend done!${NC}"

# Update docker-compose.ec2.yml automatically
echo ""
echo -e "${GREEN}🔧 Updating docker-compose.ec2.yml with your username...${NC}"

if [ -f "docker-compose.ec2.yml" ]; then
    cp docker-compose.ec2.yml docker-compose.ec2.yml.backup
    sed -i.tmp "s|YOUR_DOCKERHUB_USERNAME|$DOCKER_USERNAME|g" docker-compose.ec2.yml
    rm -f docker-compose.ec2.yml.tmp
    echo -e "${GREEN}✅ Updated docker-compose.ec2.yml${NC}"
else
    echo -e "${YELLOW}⚠️  docker-compose.ec2.yml not found, skipping.${NC}"
fi

# Success!
echo ""
echo -e "${GREEN}╔══════════════════════════════════════════════════╗${NC}"
echo -e "${GREEN}║  ✅ SUCCESS! Images built for Linux & pushed!  ║${NC}"
echo -e "${GREEN}╚══════════════════════════════════════════════════╝${NC}"
echo ""
echo -e "${YELLOW}📱 Next steps:${NC}"
echo ""
echo -e "${BLUE}1. Push to GitHub:${NC}"
echo "   git add docker-compose.ec2.yml"
echo "   git commit -m 'Update Docker Hub username'"
echo "   git push"
echo ""
echo -e "${BLUE}2. On your EC2 instance, run:${NC}"
echo "   cd /home/ubuntu/smarthire"
echo "   git pull"
echo "   docker pull $DOCKER_USERNAME/smarthire-backend:latest"
echo "   docker pull $DOCKER_USERNAME/smarthire-frontend:latest"
echo "   docker-compose -f docker-compose.ec2.yml up -d"
echo ""
echo -e "${BLUE}3. Access your app:${NC}"
echo "   Frontend: http://YOUR-EC2-IP"
echo "   Backend:  http://YOUR-EC2-IP:8000/docs"
echo ""
echo -e "${GREEN}🎉 All done! Images are EC2-compatible!${NC}"
echo ""