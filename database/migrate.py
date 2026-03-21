#!/usr/bin/env python3
"""
Run Supabase migration - Execute schema.sql on Supabase database
"""
import os
import httpx

SUPABASE_URL = os.getenv("SUPABASE_URL", "https://your-project.supabase.co")
SERVICE_KEY = os.getenv("SUPABASE_SERVICE_KEY", "your-service-key-here")

def execute_sql(sql: str):
    """Execute SQL using Supabase PostgREST query endpoint."""
    # Read schema file
    schema_path = os.path.join(os.path.dirname(__file__), "schema.sql")
    with open(schema_path) as f:
        sql_content = f.read()
    
    # Split into individual statements and execute one by one
    statements = [s.strip() for s in sql_content.split(';') if s.strip() and not s.strip().startswith('--')]
    
    print(f"🚀 Executing {len(statements)} SQL statements...")
    
    # We'll use raw SQL execution via query parameter
    # Supabase doesn't have a direct SQL exec endpoint via REST
    # We need to use the connection string with psycopg2
    
    try:
        import psycopg2
        
        # Construct connection string
        # Format: postgresql://postgres:[PASSWORD]@db.[PROJECT_REF].supabase.co:5432/postgres
        db_password = os.getenv("SUPABASE_DB_PASSWORD", SERVICE_KEY)
        project_ref = SUPABASE_URL.split("//")[1].split(".")[0] if "supabase.co" in SUPABASE_URL else "your-project"
        conn_string = f"postgresql://postgres.{project_ref}:{db_password}@aws-0-ap-southeast-1.pooler.supabase.com:6543/postgres"
        
        conn = psycopg2.connect(conn_string)
        cur = conn.cursor()
        
        for i, stmt in enumerate(statements, 1):
            if stmt:
                print(f"  [{i}/{len(statements)}] Executing: {stmt[:60]}...")
                try:
                    cur.execute(stmt)
                    conn.commit()
                    print(f"    ✅ Success")
                except Exception as e:
                    print(f"    ⚠️  {e}")
                    conn.rollback()
        
        cur.close()
        conn.close()
        print("\n✅ Migration complete!")
        
    except ImportError:
        print("❌ psycopg2 not installed. Installing...")
        os.system("pip install psycopg2-binary")
        print("\n🔄 Retrying migration...")
        execute_sql(sql)
    except Exception as e:
        print(f"❌ Migration failed: {e}")
        raise

if __name__ == "__main__":
    execute_sql("")
