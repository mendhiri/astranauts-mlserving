#!/bin/bash

# Astranauts API Deployment Script for Google Cloud Run

set -e

# Configuration
PROJECT_ID="astranauts-461014"
SERVICE_NAME="astranauts-api"
REGION="asia-southeast2"
IMAGE_NAME="gcr.io/${PROJECT_ID}/${SERVICE_NAME}"

echo "🚀 Starting deployment of Astranauts API to Cloud Run..."
echo "Project ID: ${PROJECT_ID}"
echo "Service Name: ${SERVICE_NAME}"
echo "Region: ${REGION}"

# Check if gcloud is installed and authenticated
if ! command -v gcloud &> /dev/null; then
    echo "❌ gcloud CLI is not installed. Please install it first."
    exit 1
fi

# Set the project
gcloud config set project ${PROJECT_ID}

# Enable required APIs
echo "📋 Enabling required Google Cloud APIs..."
gcloud services enable cloudbuild.googleapis.com
gcloud services enable run.googleapis.com
gcloud services enable containerregistry.googleapis.com
gcloud services enable aiplatform.googleapis.com

# Build the Docker image using Cloud Build
echo "🔨 Building Docker image with Cloud Build..."
gcloud builds submit --tag ${IMAGE_NAME}

# Deploy to Cloud Run
echo "🚀 Deploying to Cloud Run..."
gcloud run deploy ${SERVICE_NAME} \
    --image ${IMAGE_NAME} \
    --platform managed \
    --region ${REGION} \
    --allow-unauthenticated \
    --memory 2Gi \
    --cpu 1 \
    --timeout 3600 \
    --max-instances 10 \
    --set-env-vars GOOGLE_CLOUD_PROJECT=${PROJECT_ID},ENVIRONMENT=production

# Get the service URL
SERVICE_URL=$(gcloud run services describe ${SERVICE_NAME} --platform managed --region ${REGION} --format 'value(status.url)')

echo "✅ Deployment completed successfully!"
echo "🌐 Service URL: ${SERVICE_URL}"
echo "📚 API Documentation: ${SERVICE_URL}/docs"
echo "🏥 Health Check: ${SERVICE_URL}/health"

# Test the deployment
echo "🧪 Testing the deployment..."
curl -f "${SERVICE_URL}/health" || echo "⚠️  Health check failed"

echo "🎉 Astranauts API is now live!"
echo ""
echo "API Endpoints:"
echo "- Prabu (Credit Scoring): ${SERVICE_URL}/api/v1/prabu"
echo "- Sarana (OCR & NLP): ${SERVICE_URL}/api/v1/sarana"
echo "- Setia (Sentiment Analysis): ${SERVICE_URL}/api/v1/setia"
