#!/bin/bash

# Astranauts API Development Server Script

echo "🚀 Starting Astranauts API Development Server..."

# Set environment variables
export PYTHONPATH=$(pwd):$PYTHONPATH
export GOOGLE_CLOUD_PROJECT=astranauts-461014

# Load environment variables from .env
if [ -f .env ]; then
    echo "📋 Loading environment variables from .env..."
    export $(cat .env | grep -v '^#' | xargs)
fi

# Check if virtual environment exists
if [ ! -d "venv" ]; then
    echo "📦 Creating virtual environment..."
    python -m venv venv
fi

# Activate virtual environment
echo "🔧 Activating virtual environment..."
source venv/bin/activate

# Install dependencies
echo "📚 Installing dependencies..."
pip install -r requirements.txt

# Check if required directories exist
echo "📁 Creating required directories..."
mkdir -p temp_sarana_uploads
mkdir -p Output/Setia
mkdir -p Output/Prabu  
mkdir -p Output/Sarana

# Start the development server
echo "🎯 Starting FastAPI server..."
echo "📚 API Documentation will be available at: http://localhost:8080/docs"
echo "🔗 Health Check: http://localhost:8080/health"
echo ""

# Start with auto-reload for development
uvicorn app.main:app --reload --host 0.0.0.0 --port 8080 --log-level info
