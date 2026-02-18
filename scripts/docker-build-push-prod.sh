#!/bin/bash
# SmartHire - Build and Push to Docker Hub (Using docker-compose)
# Run this on your LOCAL machine (not EC2)

set -e  # Exit on error

# Colors for output
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

echo -e "${GREEN}🚀 SmartHire - Docker Hub Build & Push (Fast Mode)${NC}"
echo -e "${BLUE}Using docker-compose for parallel builds${NC}"
echo ""

# Get Docker Hub username
read -p "Enter your Docker Hub username: " DOCKER_USERNAME

if [ -z "$DOCKER_USERNAME" ]; then
    echo -e "${RED}❌ Docker Hub username is required!${NC}"
    exit 1
fi

echo ""
echo -e "${YELLOW}📋 Summary:${NC}"
echo "  Backend image: $DOCKER_USERNAME/smarthire-backend:latest"
echo "  Frontend image: $DOCKER_USERNAME/smarthire-frontend:latest"
echo "  Build method: docker-compose (parallel build - faster!)"
echo ""
read -p "Continue? (y/n) " -n 1 -r
echo
if [[ ! $REPLY =~ ^[Yy]$ ]]; then
    echo "Cancelled."
    exit 1
fi

# Check if logged in to Docker Hub
echo ""
echo -e "${GREEN}🔐 Checking Docker Hub login...${NC}"
if ! docker info | grep -q "Username"; then
    echo -e "${YELLOW}Please login to Docker Hub:${NC}"
    docker login
fi

# Build both images using docker-compose (parallel build!)
echo ""
echo -e "${GREEN}🏗️  Building both images in parallel...${NC}"
echo -e "${BLUE}This is faster than building separately!${NC}"
docker-compose -f docker-compose.prod.yml build

if [ $? -ne 0 ]; then
    echo -e "${RED}❌ Build failed!${NC}"
    exit 1
fi

echo -e "${GREEN}✅ Build successful!${NC}"

# Tag images for Docker Hub
echo ""
echo -e "${GREEN}🏷️  Tagging images for Docker Hub...${NC}"

# Get the actual image names created by docker-compose
BACKEND_IMAGE=$(docker images --format "{{.Repository}}:{{.Tag}}" | grep smarthire-backend | head -1)
FRONTEND_IMAGE=$(docker images --format "{{.Repository}}:{{.Tag}}" | grep smarthire-frontend | head -1)

if [ -z "$BACKEND_IMAGE" ] || [ -z "$FRONTEND_IMAGE" ]; then
    echo -e "${RED}❌ Could not find built images!${NC}"
    echo "Looking for images..."
    docker images | grep smarthire
    exit 1
fi

echo "  Found backend: $BACKEND_IMAGE"
echo "  Found frontend: $FRONTEND_IMAGE"

docker tag $BACKEND_IMAGE $DOCKER_USERNAME/smarthire-backend:latest
docker tag $FRONTEND_IMAGE $DOCKER_USERNAME/smarthire-frontend:latest

echo -e "${GREEN}✅ Tagged successfully!${NC}"

# Push backend
echo ""
echo -e "${GREEN}⬆️  Pushing backend to Docker Hub...${NC}"
docker push $DOCKER_USERNAME/smarthire-backend:latest

if [ $? -ne 0 ]; then
    echo -e "${RED}❌ Backend push failed!${NC}"
    exit 1
fi

# Push frontend
echo ""
echo -e "${GREEN}⬆️  Pushing frontend to Docker Hub...${NC}"
docker push $DOCKER_USERNAME/smarthire-frontend:latest

if [ $? -ne 0 ]; then
    echo -e "${RED}❌ Frontend push failed!${NC}"
    exit 1
fi

# Update docker-compose.ec2.yml automatically
echo ""
echo -e "${GREEN}🔧 Generating docker-compose.ec2.yml from template...${NC}"

if [ -f "docker-compose.ec2.template.yml" ]; then
    # Copy template → actual file
    cp docker-compose.ec2.template.yml docker-compose.ec2.yml

    # Replace Docker Hub username
    sed -i.tmp "s|YOUR_DOCKERHUB_USERNAME|$DOCKER_USERNAME|g" docker-compose.ec2.yml
    rm -f docker-compose.ec2.yml.tmp

    echo -e "${GREEN}✅ docker-compose.ec2.yml generated and updated${NC}"
else
    echo -e "${RED}❌ docker-compose.ec2.template.yml not found!${NC}"
    exit 1
fi

# Success!
echo ""
echo -e "${GREEN}╔════════════════════════════════════════════╗${NC}"
echo -e "${GREEN}║  ✅ SUCCESS! Images are on Docker Hub!    ║${NC}"
echo -e "${GREEN}╚════════════════════════════════════════════╝${NC}"
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
echo -e "${GREEN}🎉 All done!${NC}"
echo ""

# Show image sizes
echo -e "${YELLOW}📦 Image sizes:${NC}"
docker images | grep $DOCKER_USERNAME/smarthire
echo ""

