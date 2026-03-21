#!/usr/bin/env python3
"""
Alternative: Execute migration using Supabase Management API
Since we can't execute raw SQL via REST, we'll document the manual steps
and provide a Python-based solution using the service key.
"""
import httpx
import sys
import os

SUPABASE_URL = os.getenv("SUPABASE_URL", "https://your-project.supabase.co")
SERVICE_KEY = os.getenv("SUPABASE_SERVICE_KEY", "your-service-key-here")

print("""
╔════════════════════════════════════════════════════════════════════╗
║  CrawlKit Supabase Migration Instructions                         ║
╚════════════════════════════════════════════════════════════════════╝

To execute the database schema, please follow these steps:

1. Go to: https://supabase.com/dashboard/project/YOUR_PROJECT_REF/sql/new

2. Copy the contents of database/schema.sql

3. Paste into the SQL Editor and click "Run"

Alternatively, if you have the Supabase CLI installed:
   
   supabase db reset --db-url "postgresql://postgres:[PASSWORD]@db.YOUR_PROJECT_REF.supabase.co:5432/postgres"

Or use psql directly:
   
   psql "postgresql://postgres:[PASSWORD]@db.YOUR_PROJECT_REF.supabase.co:5432/postgres" < database/schema.sql

══════════════════════════════════════════════════════════════════════

⚠️  Note: The service_role key only works with Supabase's REST API,
   not direct PostgreSQL connections. You need the database password
   for psql/psycopg2 connections.

══════════════════════════════════════════════════════════════════════
""")

# Verify we can at least access the REST API
print("🔍 Testing Supabase REST API access...")
try:
    client = httpx.Client(
        base_url=SUPABASE_URL,
        headers={
            "apikey": SERVICE_KEY,
            "Authorization": f"Bearer {SERVICE_KEY}",
        },
        timeout=10.0,
    )
    
    resp = client.get("/rest/v1/")
    if resp.status_code in [200, 404, 401]:
        print("✅ Supabase REST API is accessible")
        print(f"   Status: {resp.status_code}")
    else:
        print(f"⚠️  Unexpected response: {resp.status_code}")
        print(f"   {resp.text[:200]}")
    
    client.close()
    
except Exception as e:
    print(f"❌ API connection failed: {e}")
    sys.exit(1)

print("\n📋 Schema file location: database/schema.sql")
print("📝 Please run the SQL manually via Supabase Dashboard SQL Editor")
print("\nOnce complete, proceed with the rest of the setup ✅")
