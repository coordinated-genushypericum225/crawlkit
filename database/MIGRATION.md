# CrawlKit Database Migration

## Overview

CrawlKit now includes a built-in migration system that can be run from Railway (where PostgreSQL port is accessible).

## Migration Methods

### Method 1: API Endpoint (Recommended)

Once deployed to Railway, trigger the migration via API:

```bash
curl -X POST https://your-app.railway.app/v1/admin/migrate \
  -H "Authorization: Bearer $CRAWLKIT_MASTER_KEY"
```

**Response:**
```json
{
  "success": true,
  "message": "Migration completed successfully",
  "statements_executed": 25
}
```

This endpoint:
- ✅ Protected by master key authentication
- ✅ Safe to run multiple times (uses `IF NOT EXISTS`)
- ✅ Executes all statements in `database/schema.sql`
- ✅ Can be triggered from any environment (local, CI, etc.)

### Method 2: Python Script

Alternatively, run the migration script directly from Railway:

```bash
# SSH into Railway container
railway run python scripts/migrate.py
```

**Environment Variables Required:**

Either:
- `DATABASE_URL` — Full PostgreSQL connection string

Or:
- `SUPABASE_URL` — Your Supabase project URL
- `SUPABASE_DB_PASSWORD` — Database password (not service key!)

Get the database password from:
**Supabase Dashboard → Settings → Database → Connection String**

## Schema Changes

Latest migration adds:

### `ck_payment_requests`
Payment request tracking for plan upgrades.

### `ck_settings`
Global application settings (bank info, pricing).

**Default settings:**
- `bank_id`, `bank_account`, `bank_holder` — Bank details for VND payments
- `price_starter_vnd`, `price_pro_vnd` — Pricing in Vietnamese Dong

## Troubleshooting

### ❌ "psycopg2 not installed"
```bash
pip install psycopg2-binary
```

### ❌ "SUPABASE_DB_PASSWORD not set"
Get password from Supabase Dashboard → Settings → Database.

**Note:** This is NOT the same as your service key!

### ❌ "Connection failed: timeout"
PostgreSQL port 5432 might be blocked. Use the API endpoint method instead (it runs from Railway where the port IS accessible).

## Files

- `database/schema.sql` — Source of truth for schema
- `scripts/migrate.py` — Standalone migration script
- `crawlkit/api/server.py` — Contains `/v1/admin/migrate` endpoint

## Security

- Migration endpoint requires master key (`CRAWLKIT_MASTER_KEY`)
- All statements use `IF NOT EXISTS` — safe to re-run
- ROW LEVEL SECURITY enabled on all user-facing tables
