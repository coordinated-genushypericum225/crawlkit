#!/usr/bin/env python3
"""
CrawlKit Database Migration Script
Reads schema.sql and executes it against Supabase PostgreSQL.
"""

import os
import sys
from pathlib import Path

try:
    import psycopg2
except ImportError:
    print("❌ psycopg2 not installed. Run: pip install psycopg2-binary")
    sys.exit(1)


def get_database_url():
    """Get database URL from environment or construct from Supabase config."""
    # Try DATABASE_URL first
    db_url = os.getenv("DATABASE_URL")
    if db_url:
        return db_url
    
    # Construct from Supabase components
    supabase_url = os.getenv("SUPABASE_URL", "https://your-project.supabase.co")
    supabase_key = os.getenv("SUPABASE_SERVICE_KEY")
    
    # Extract project ref from URL
    if "supabase.co" not in supabase_url:
        print("⚠️  Invalid SUPABASE_URL format")
        return None
        
    project_ref = supabase_url.split("//")[1].split(".")[0]
    
    # Supabase PostgreSQL connection string format
    # postgres://postgres:[YOUR-PASSWORD]@db.[PROJECT-REF].supabase.co:5432/postgres
    db_password = os.getenv("SUPABASE_DB_PASSWORD")
    if not db_password:
        print("⚠️  SUPABASE_DB_PASSWORD not set. This is your database password (not the service key).")
        print("    Find it in Supabase Dashboard → Settings → Database → Connection String")
        return None
    
    return f"postgres://postgres:{db_password}@db.{project_ref}.supabase.co:5432/postgres"


def run_migration(conn, sql_content):
    """Execute SQL migration."""
    with conn.cursor() as cur:
        try:
            # Split by semicolons but keep them
            statements = [s.strip() for s in sql_content.split(';') if s.strip()]
            
            for i, statement in enumerate(statements, 1):
                if not statement:
                    continue
                    
                print(f"  Executing statement {i}/{len(statements)}...", end=" ")
                cur.execute(statement)
                print("✓")
            
            conn.commit()
            print("\n✅ Migration completed successfully!")
            return True
            
        except Exception as e:
            conn.rollback()
            print(f"\n❌ Migration failed: {e}")
            return False


def main():
    """Main migration function."""
    print("🔄 CrawlKit Database Migration")
    print("=" * 50)
    
    # Get database URL
    db_url = get_database_url()
    if not db_url:
        return False
    
    # Read schema.sql
    schema_path = Path(__file__).parent.parent / "database" / "schema.sql"
    if not schema_path.exists():
        print(f"❌ Schema file not found: {schema_path}")
        return False
    
    print(f"📖 Reading schema from: {schema_path}")
    sql_content = schema_path.read_text()
    
    # Connect and migrate
    try:
        print(f"🔌 Connecting to database...")
        conn = psycopg2.connect(db_url)
        print("✓ Connected")
        
        print("\n🚀 Running migration...")
        success = run_migration(conn, sql_content)
        
        conn.close()
        return success
        
    except psycopg2.OperationalError as e:
        print(f"❌ Connection failed: {e}")
        print("\n💡 Tips:")
        print("  - Check SUPABASE_DB_PASSWORD is correct")
        print("  - Verify PostgreSQL port 5432 is accessible from this environment")
        print("  - If on Railway, this should work automatically")
        return False
    except Exception as e:
        print(f"❌ Unexpected error: {e}")
        return False


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
