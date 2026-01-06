# Cron Job Setup Guide

This document explains how to set up and use the automated cron job system for syncing centers and running batch processes.

## Overview

The cron job system automatically:
1. Fetches a list of center slugs from `LOCATION_SLUG_API_URL`
2. For each slug, fetches center details using `LOCATION_DATA_API_URL`
3. Stores center data in the database
4. Runs the batch process for all active centers

## Configuration

### Environment Variables

Add these to your `.env.stage` or `.env.production` file:

```bash
# Location API Configuration
LOCATION_SLUG_API_URL=https://your-api.com/locations/slugs
LOCATION_DATA_API_URL=https://your-api.com/location/data
LOCATION_API_KEY=your-api-key-here  # Optional

# Database Configuration
DATABASE_URL=sqlite:///data/centers.db  # SQLite (default)
# Or use PostgreSQL:
# DATABASE_URL=postgresql://user:password@localhost/dbname

# Cron Job Configuration
CRON_ENABLED=true  # Enable/disable cron jobs
CRON_SCHEDULE=*/5 * * * *  # Every 5 minutes (default)

# Email Test Mode Configuration (for stage environment testing)
EMAIL_SEND_TO_OWNERS=false  # If false, send to test email instead of center owners
EMAIL_TEST_RECIPIENT=test@example.com  # Test email address (used when EMAIL_SEND_TO_OWNERS=false)
TEST_MODE_LIMIT_CENTERS=5  # Limit number of centers to process in stage environment (0 = no limit)

# Database Sync Configuration
SYNC_TO_DATABASE=false  # If true, sync centers to database and use database. If false, fetch directly from APIs (no database)
```

### Cron Schedule Format

The `CRON_SCHEDULE` uses standard cron expression format:
```
minute hour day month day_of_week
```

**Examples:**
- `*/5 * * * *` - Every 5 minutes (default)
- `*/30 * * * *` - Every 30 minutes
- `0 2 * * *` - Daily at 2:00 AM
- `0 */6 * * *` - Every 6 hours
- `0 0 * * 0` - Weekly on Sunday at midnight
- `0 0 1 * *` - Monthly on the 1st at midnight

## Test Mode Configuration (Stage Environment)

For testing purposes in the stage environment, you can configure the system to:

1. **Limit the number of centers processed**: Set `TEST_MODE_LIMIT_CENTERS=5` to only process the first 5 centers
2. **Send emails to a test address**: Set `EMAIL_SEND_TO_OWNERS=false` and provide `EMAIL_TEST_RECIPIENT` to send all emails to a test address instead of center owners
3. **Use database or fetch directly from APIs**: Set `SYNC_TO_DATABASE=false` to fetch centers directly from APIs without storing in database

**Example Configuration for Testing:**
```bash
# In .env.stage
APP_ENV=stage
EMAIL_SEND_TO_OWNERS=false
EMAIL_TEST_RECIPIENT=your-test-email@example.com
TEST_MODE_LIMIT_CENTERS=5
SYNC_TO_DATABASE=false  # Fetch directly from APIs, no database sync
```

**How it works:**
- When `EMAIL_SEND_TO_OWNERS=false`, all emails are sent to `EMAIL_TEST_RECIPIENT` instead of center owner emails
- Email subjects will be prefixed with `[TEST]` to indicate test mode
- In stage environment, only the first N centers (specified by `TEST_MODE_LIMIT_CENTERS`) will be processed
- Set `TEST_MODE_LIMIT_CENTERS=0` to disable the limit (process all centers)
- When `SYNC_TO_DATABASE=false`, centers are fetched directly from APIs on each run without storing in database
- When `SYNC_TO_DATABASE=true`, centers are synced to database first, then retrieved from database for processing

**Production Configuration:**
```bash
# In .env.production
APP_ENV=production
EMAIL_SEND_TO_OWNERS=true
TEST_MODE_LIMIT_CENTERS=0  # Process all centers
SYNC_TO_DATABASE=true  # Use database for persistence
```

## How It Works

### 1. Center Sync Process

The system fetches centers in two steps:

**Step 1: Fetch Center Slugs**
- Calls `LOCATION_SLUG_API_URL` to get a list of all center slugs
- Handles various response formats (list, dict with data/results, etc.)

**Step 2: Fetch Center Details**
- For each slug, calls `LOCATION_DATA_API_URL/slug/{slug}` to get full details
- Extracts center information (name, location, email, etc.)
- Stores in database

### 2. Database Storage

Centers are stored in the `centers` table with the following fields:
- `center_id`: Unique identifier
- `center_name`: Name of the center
- `slug`: Location slug
- `zip_code`, `city`, `state`, `country`: Location information
- `radius`: Search radius for events (default: 5 miles)
- `owner_email`: Center owner email
- `location_data`: Full JSON data from API
- `is_active`: Whether center is active
- `created_at`, `updated_at`: Timestamps

### 3. Batch Process

After syncing centers, the system:
- Retrieves all active centers from database
- Converts them to `CenterInfo` format
- Creates a batch run
- Processes all centers through the event discovery system
- Generates CSV files for each center

## API Endpoints

### Manual Triggers

You can manually trigger the cron job processes using these endpoints:

#### 1. Sync Centers Only
```bash
POST /cron/sync-centers
```

Syncs centers from APIs to database without running batch process.

**Response:**
```json
{
  "status": "success",
  "message": "Successfully synced 25 centers",
  "synced_count": 25
}
```

#### 2. Run Batch Only
```bash
POST /cron/run-batch
```

Runs batch process for all active centers in database (without syncing).

**Response:**
```json
{
  "run_id": "batch_1234567890",
  "status": "running",
  "message": "Batch run started for 25 centers",
  "started_at": "2024-01-15T02:00:00"
}
```

#### 3. Sync and Run (Full Process)
```bash
POST /cron/sync-and-run
```

Runs the complete process: sync centers + run batch.

**Response:**
```json
{
  "status": "success",
  "message": "Synced 25 centers and started batch run for 25 centers",
  "synced_count": 25,
  "batch_run_id": "batch_1234567890",
  "centers_count": 25
}
```

#### 4. Check Cron Status
```bash
GET /cron/status
```

Get current cron service status and next run time.

**Response:**
```json
{
  "enabled": true,
  "next_run_time": "2024-01-16T02:00:00",
  "is_running": false
}
```

### Batch Run Status

Check the status of a batch run:
```bash
GET /events/status/{run_id}
```

## Database Setup

The database is automatically initialized when the application starts. Tables are created if they don't exist.

### Database Models

**Centers Table:**
- Stores center information synced from APIs
- Automatically updated when centers are synced

**Batch Runs Table:**
- Tracks batch run history
- Stores status, counts, and error messages

## Installation

1. **Install Dependencies:**
   ```bash
   pip install -r requirements.txt
   ```

2. **Configure Environment:**
   - Set `LOCATION_SLUG_API_URL` and `LOCATION_DATA_API_URL`
   - Set `CRON_ENABLED=true` to enable cron jobs
   - Configure `CRON_SCHEDULE` as needed

3. **Start Application:**
   ```bash
   uvicorn app.main:app --reload
   ```

The cron service will start automatically if `CRON_ENABLED=true`.

## Troubleshooting

### Cron Job Not Running

1. Check if cron is enabled:
   ```bash
   curl http://localhost:8000/cron/status
   ```

2. Check logs for errors:
   ```bash
   # Look for cron service startup messages
   # Check for API connection errors
   ```

3. Verify API URLs are correct:
   - Test `LOCATION_SLUG_API_URL` manually
   - Test `LOCATION_DATA_API_URL` with a sample slug

### Database Issues

1. Check database file exists:
   ```bash
   ls -la data/centers.db  # SQLite
   ```

2. Verify database URL in config:
   ```bash
   # Check .env file
   DATABASE_URL=sqlite:///data/centers.db
   ```

### API Connection Issues

1. Verify API endpoints are accessible
2. Check API key is correct (if required)
3. Review timeout settings (default: 30 seconds)

## Monitoring

### Logs

The cron job logs all activities:
- Center sync progress
- Batch run status
- Errors and warnings

### Database Queries

Check centers in database:
```python
from app.database import get_db_session, Center

db = get_db_session()
centers = db.query(Center).filter(Center.is_active == True).all()
print(f"Active centers: {len(centers)}")
```

## Best Practices

1. **Schedule Wisely**: Run during low-traffic hours (e.g., 2 AM)
2. **Monitor First Runs**: Check logs after first automated run
3. **Test Manually**: Use manual endpoints to test before enabling cron
4. **Backup Database**: Regularly backup the centers database
5. **Error Handling**: Monitor logs for API failures or database errors

## Disabling Cron Jobs

To disable cron jobs:

1. Set in environment:
   ```bash
   CRON_ENABLED=false
   ```

2. Or comment out in code (not recommended)

The application will still work, but automated syncing and batch runs won't occur.

