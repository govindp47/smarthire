#!/bin/bash
# SmartHire - Development Docker Setup

set -e

echo "🚀 Starting SmartHire in Development Mode..."

# Check if .env exists
if [ ! -f .env ]; then
    echo "📝 Creating .env from .env.docker.example..."
    cp .env.docker.example .env
    echo "⚠️  Please update .env with your OpenAI API key!"
    exit 1
fi

# Build and start services
echo "🏗️  Building Docker images..."
docker-compose build

echo "🚀 Starting services..."
docker-compose up -d

echo "⏳ Waiting for services to be healthy..."
sleep 10

# Check service status
echo "📊 Service Status:"
docker-compose ps

echo ""
echo "✅ SmartHire is running!"
echo ""
echo "📱 Frontend: http://localhost"
echo "🔧 Backend API: http://localhost:8000"
echo "📚 API Docs: http://localhost:8000/docs"
echo ""
echo "📋 Useful commands:"
echo "  View logs: docker-compose logs -f"
echo "  Stop: docker-compose down"
echo "  Restart: docker-compose restart"
echo ""
