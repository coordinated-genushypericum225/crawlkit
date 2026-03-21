#!/bin/bash

# Set Railway environment variables for CrawlKit Supabase integration

RAILWAY_TOKEN="${RAILWAY_TOKEN:-your-railway-token}"
PROJECT_ID="${RAILWAY_PROJECT_ID:-your-project-id}"
ENVIRONMENT_ID="${RAILWAY_ENVIRONMENT_ID:-your-environment-id}"
SERVICE_ID="${RAILWAY_SERVICE_ID:-your-service-id}"

# Function to set a variable
set_var() {
    local name=$1
    local value=$2
    
    echo "Setting $name..."
    
    curl -X POST https://backboard.railway.app/graphql/v2 \
      -H "Authorization: Bearer $RAILWAY_TOKEN" \
      -H "Content-Type: application/json" \
      -d "{
        \"query\": \"mutation { variableCollectionUpsert(input: { environmentId: \\\"$ENVIRONMENT_ID\\\", serviceId: \\\"$SERVICE_ID\\\", variables: { $name: \\\"$value\\\" } }) }\",
      }" 2>&1 | jq -r '.data // .errors'
}

# Set variables from environment
SUPABASE_URL="${SUPABASE_URL:-https://your-project.supabase.co}"
SUPABASE_SERVICE_KEY="${SUPABASE_SERVICE_KEY:-your-service-key}"

set_var "SUPABASE_URL" "$SUPABASE_URL"
set_var "SUPABASE_SERVICE_KEY" "$SUPABASE_SERVICE_KEY"

echo ""
echo "✅ Environment variables set!"
echo "Please manually verify in Railway dashboard:"
echo "https://railway.app/project/$PROJECT_ID/service/$SERVICE_ID"
