#!/usr/bin/env python3
"""
Set Railway environment variables via GraphQL API
"""
import httpx
import json
import os

RAILWAY_TOKEN = os.getenv("RAILWAY_TOKEN", "your-railway-token-here")
PROJECT_ID = os.getenv("RAILWAY_PROJECT_ID", "your-project-id")
ENVIRONMENT_ID = os.getenv("RAILWAY_ENVIRONMENT_ID", "your-environment-id")
SERVICE_ID = os.getenv("RAILWAY_SERVICE_ID", "your-service-id")

VARIABLES = {
    "SUPABASE_URL": os.getenv("SUPABASE_URL", "https://your-project.supabase.co"),
    "SUPABASE_SERVICE_KEY": os.getenv("SUPABASE_SERVICE_KEY", "your-supabase-service-key"),
}

def set_variables():
    """Set all environment variables using Railway GraphQL API."""
    
    client = httpx.Client(
        base_url="https://backboard.railway.app/graphql/v2",
        headers={
            "Authorization": f"Bearer {RAILWAY_TOKEN}",
            "Content-Type": "application/json",
        },
        timeout=30.0,
    )
    
    # Use variableCollectionUpsert to set multiple variables at once
    variables_json = json.dumps(VARIABLES)
    
    query = """
    mutation VariableCollectionUpsert($input: VariableCollectionUpsertInput!) {
      variableCollectionUpsert(input: $input)
    }
    """
    
    payload = {
        "query": query,
        "variables": {
            "input": {
                "environmentId": ENVIRONMENT_ID,
                "serviceId": SERVICE_ID,
                "variables": VARIABLES,
            }
        }
    }
    
    print("🚀 Setting Railway environment variables...")
    print(f"   Project: {PROJECT_ID}")
    print(f"   Environment: {ENVIRONMENT_ID}")
    print(f"   Service: {SERVICE_ID}")
    print()
    
    for key in VARIABLES:
        print(f"   • {key}")
    print()
    
    try:
        resp = client.post("", json=payload)
        resp.raise_for_status()
        
        result = resp.json()
        
        if "errors" in result:
            print("❌ Error from Railway API:")
            print(json.dumps(result["errors"], indent=2))
            return False
        
        if "data" in result:
            print("✅ Environment variables set successfully!")
            print()
            print("Verify at:")
            print(f"https://railway.app/project/{PROJECT_ID}/service/{SERVICE_ID}")
            return True
        
        print("⚠️  Unexpected response:")
        print(json.dumps(result, indent=2))
        return False
    
    except httpx.HTTPStatusError as e:
        print(f"❌ HTTP error: {e.response.status_code}")
        print(e.response.text)
        return False
    
    except Exception as e:
        print(f"❌ Error: {e}")
        return False
    
    finally:
        client.close()


if __name__ == "__main__":
    success = set_variables()
    
    if not success:
        print()
        print("⚠️  If API method fails, set variables manually:")
        print()
        print(f"1. Go to https://railway.app/project/{PROJECT_ID}/service/{SERVICE_ID}")
        print("2. Go to Variables tab")
        print("3. Add these variables:")
        print()
        for key, value in VARIABLES.items():
            print(f"   {key} = {value}")
        print()
