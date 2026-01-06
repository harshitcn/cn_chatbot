# Automation System Presentation - Center Sync & Batch Processing

## Executive Summary

This document presents the complete automation system for syncing center data and running batch event discovery processes. The system operates both automatically (via cron jobs) and manually (via API endpoints).

---

## System Overview

### What It Does

1. **Automatically syncs center data** from external APIs to our database
2. **Runs batch event discovery** for all active centers
3. **Generates CSV reports** for each center
4. **Tracks all operations** in the database

### Key Features

- ✅ **Fully Automated**: Runs on schedule (default: daily at 2 AM)
- ✅ **Manual Control**: API endpoints for on-demand execution
- ✅ **Error Resilient**: Handles failures gracefully
- ✅ **Trackable**: Complete audit trail in database
- ✅ **Scalable**: Processes multiple centers efficiently

---

## Architecture Diagram

### High-Level Flow

```
┌─────────────────────────────────────────────────────────────┐
│                    SYSTEM STARTUP                            │
│  • Load Configuration                                         │
│  • Initialize Database                                        │
│  • Start Cron Scheduler                                       │
└─────────────────────────────────────────────────────────────┘
                          │
                          ▼
┌─────────────────────────────────────────────────────────────┐
│              AUTOMATED CRON JOB (Daily 2 AM)                │
│              OR MANUAL TRIGGER (API Endpoint)               │
└─────────────────────────────────────────────────────────────┘
                          │
                          ▼
┌─────────────────────────────────────────────────────────────┐
│              STEP 1: SYNC CENTERS FROM APIs                  │
│                                                               │
│  1. Fetch Center Slugs                                       │
│     └─> LOCATION_SLUG_API_URL                                │
│                                                               │
│  2. For Each Slug, Fetch Details                             │
│     └─> LOCATION_DATA_API_URL/slug/{slug}                    │
│                                                               │
│  3. Store/Update in Database                                 │
│     └─> centers table                                        │
└─────────────────────────────────────────────────────────────┘
                          │
                          ▼
┌─────────────────────────────────────────────────────────────┐
│              STEP 2: BATCH EVENT DISCOVERY                   │
│                                                               │
│  1. Get All Active Centers from Database                    │
│                                                               │
│  2. For Each Center:                                         │
│     • Build Location String                                  │
│     • Generate LLM Prompt                                    │
│     • Call LLM API (Grok/OpenAI)                             │
│     • Parse Events from Response                             │
│     • Generate CSV File                                      │
│                                                               │
│  3. Update Batch Run Status                                  │
│     └─> batch_runs table                                    │
└─────────────────────────────────────────────────────────────┘
                          │
                          ▼
┌─────────────────────────────────────────────────────────────┐
│                    COMPLETION                                │
│  • All Centers Processed                                    │
│  • CSV Files Generated                                      │
│  • Status Updated in Database                                │
│  • Next Run Scheduled                                        │
└─────────────────────────────────────────────────────────────┘
```

---

## Detailed Component Flow

### 1. Center Sync Process

```
┌──────────────┐
│  Start Sync  │
└──────┬───────┘
       │
       ▼
┌─────────────────────┐      ┌──────────────────┐
│ Call Slug API       │─────>│ LOCATION_SLUG_    │
│ GET Request         │      │ API_URL           │
└──────┬──────────────┘      └────────┬──────────┘
       │                              │
       │                              │ Returns
       │                              │ List of Slugs
       │                              │
       ▼                              │
┌─────────────────────┐              │
│ Parse Response       │<─────────────┘
│ Extract Slugs        │
└──────┬───────────────┘
       │
       │ For Each Slug
       ▼
┌─────────────────────┐      ┌──────────────────┐
│ Call Data API       │─────>│ LOCATION_DATA_    │
│ GET /slug/{slug}    │      │ API_URL           │
└──────┬──────────────┘      └────────┬──────────┘
       │                              │
       │                              │ Returns
       │                              │ Center Details
       │                              │
       ▼                              │
┌─────────────────────┐              │
│ Extract Center Info │<─────────────┘
│ - center_id         │
│ - center_name       │
│ - city, state, zip │
│ - owner_email       │
└──────┬──────────────┘
       │
       ▼
┌─────────────────────┐
│ Check Database      │
│ Center Exists?      │
└──────┬──────────────┘
       │
       ├─ Yes ──> UPDATE centers
       │
       └─ No  ──> INSERT INTO centers
       │
       ▼
┌─────────────────────┐
│ Commit Transaction  │
└─────────────────────┘
```

### 2. Batch Processing Flow

```
┌─────────────────────┐
│ Get Active Centers │
│ FROM centers        │
│ WHERE is_active=1   │
└──────┬──────────────┘
       │
       ▼
┌─────────────────────┐
│ Create Batch Run    │
│ Generate run_id      │
│ Status: running     │
└──────┬──────────────┘
       │
       │ For Each Center
       ▼
┌─────────────────────┐
│ Build Location      │
│ "zip, city, state"  │
└──────┬──────────────┘
       │
       ▼
┌─────────────────────┐
│ Generate LLM Prompt │
│ Using Template      │
└──────┬──────────────┘
       │
       ▼
┌─────────────────────┐      ┌──────────────┐
│ Call LLM API        │─────>│ Grok/OpenAI  │
│ Query Events        │      │ API          │
└──────┬──────────────┘      └──────┬───────┘
       │                            │
       │                            │ Returns
       │                            │ Events Data
       │                            │
       ▼                            │
┌─────────────────────┐            │
│ Parse Events        │<───────────┘
│ Extract Event Info  │
└──────┬──────────────┘
       │
       ▼
┌─────────────────────┐
│ Generate CSV File   │
│ Save to data/events/ │
└──────┬──────────────┘
       │
       ▼
┌─────────────────────┐
│ Update Batch Status  │
│ processed_centers++  │
│ successful_centers++  │
└──────┬──────────────┘
       │
       │ More Centers?
       ├─ Yes ──> Loop Back
       │
       └─ No
       │
       ▼
┌─────────────────────┐
│ Mark Batch Complete │
│ Status: completed    │
└─────────────────────┘
```

---

## API Endpoints

### Automated Endpoints (Cron)

| Endpoint | Method | Description | Trigger |
|----------|--------|-------------|---------|
| Auto Sync & Batch | Cron | Full automation process | Scheduled (default: 2 AM daily) |

### Manual Endpoints

| Endpoint | Method | Description | Use Case |
|----------|--------|-------------|----------|
| `/cron/sync-centers` | POST | Sync centers from APIs only | Initial setup, refresh data |
| `/cron/run-batch` | POST | Run batch for existing centers | Re-run batch without sync |
| `/cron/sync-and-run` | POST | Full process (sync + batch) | Complete manual trigger |
| `/cron/status` | GET | Check cron service status | Monitoring |
| `/events/status/{run_id}` | GET | Check batch run status | Track progress |

### Example API Calls

```bash
# Manual Sync Centers
curl -X POST http://localhost:8000/cron/sync-centers

# Manual Full Process
curl -X POST http://localhost:8000/cron/sync-and-run

# Check Cron Status
curl http://localhost:8000/cron/status

# Check Batch Status
curl http://localhost:8000/events/status/batch_1234567890
```

---

## Database Schema

### Centers Table

| Column | Type | Description |
|--------|------|-------------|
| id | Integer | Primary key |
| center_id | String | Unique center identifier |
| center_name | String | Center name |
| slug | String | Location slug (indexed) |
| zip_code | String | ZIP/postal code |
| city | String | City name |
| state | String | State/province |
| country | String | Country (default: USA) |
| radius | Integer | Search radius in miles |
| owner_email | String | Center owner email |
| location_data | Text | Full JSON from API |
| is_active | Boolean | Active status |
| created_at | DateTime | Creation timestamp |
| updated_at | DateTime | Last update timestamp |

### Batch Runs Table

| Column | Type | Description |
|--------|------|-------------|
| id | Integer | Primary key |
| run_id | String | Unique run identifier |
| status | String | running/completed/failed |
| total_centers | Integer | Total centers to process |
| processed_centers | Integer | Centers processed |
| successful_centers | Integer | Successful discoveries |
| failed_centers | Integer | Failed discoveries |
| started_at | DateTime | Start timestamp |
| completed_at | DateTime | Completion timestamp |
| error_message | Text | Error details (if failed) |

---

## Configuration

### Environment Variables

```bash
# Required
LOCATION_SLUG_API_URL=https://api.example.com/locations/slugs
LOCATION_DATA_API_URL=https://api.example.com/location/data

# Optional
LOCATION_API_KEY=your-api-key-here

# Cron Configuration
CRON_ENABLED=true
CRON_SCHEDULE=0 2 * * *  # Daily at 2 AM

# Database
DATABASE_URL=sqlite:///data/centers.db
```

### Cron Schedule Examples

| Schedule | Expression | Description |
|----------|------------|-------------|
| Daily 2 AM | `0 2 * * *` | Every day at 2:00 AM |
| Every 6 Hours | `0 */6 * * *` | At 00:00, 06:00, 12:00, 18:00 |
| Weekly Sunday | `0 0 * * 0` | Every Sunday at midnight |
| Monthly 1st | `0 0 1 * *` | First day of month at midnight |
| Every 30 Minutes | `*/30 * * * *` | Every 30 minutes |

---

## Execution Timeline Example

### Typical Daily Run (25 Centers)

```
02:00:00 - Cron Triggered
02:00:01 - Fetching center slugs (API call)
02:00:03 - Received 25 slugs
02:00:04 - Fetching details for center 1
02:00:05 - Fetching details for center 2
...
02:01:30 - All 25 centers synced to database
02:01:31 - Starting batch run
02:01:32 - Processing center 1 (LLM call)
02:02:15 - Processing center 2 (LLM call)
...
02:45:00 - Batch run complete
           - 25 centers processed
           - 25 CSV files generated
           - Status: completed
02:45:01 - Next run scheduled: 02:00:00 (next day)
```

**Total Time**: ~45 minutes for 25 centers
**API Calls**: 
- 1 call to slug API
- 25 calls to data API
- 25 calls to LLM API

---

## Error Handling

### Resilience Features

1. **API Failures**: 
   - Logged and skipped
   - Center marked as failed
   - Process continues with next center

2. **Database Errors**:
   - Transaction rollback
   - Error logged
   - Retry on next run

3. **LLM Failures**:
   - Fallback CSV generated
   - Status marked as partial/failed
   - Batch continues

### Error Flow

```
Operation
    │
    ├─ Success ──> Continue
    │
    └─ Error ──> Log Error
                 │
                 ├─ Retryable? ──> Retry (max 3 times)
                 │
                 └─ Not Retryable ──> Skip & Continue
```

---

## Monitoring & Status

### Status Endpoints

**Cron Status:**
```json
{
  "enabled": true,
  "next_run_time": "2024-01-16T02:00:00",
  "is_running": false
}
```

**Batch Run Status:**
```json
{
  "run_id": "batch_1234567890",
  "status": "completed",
  "total_centers": 25,
  "processed_centers": 25,
  "successful_centers": 23,
  "failed_centers": 2,
  "started_at": "2024-01-15T02:00:00",
  "completed_at": "2024-01-15T02:45:00"
}
```

---

## Benefits

### For Operations Team
- ✅ **Zero Manual Work**: Fully automated
- ✅ **Consistent Schedule**: Runs on time, every time
- ✅ **Error Tracking**: Complete audit trail
- ✅ **Manual Override**: Can trigger anytime via API

### For Development Team
- ✅ **Modular Design**: Easy to extend
- ✅ **Well Documented**: Clear code structure
- ✅ **Testable**: Manual endpoints for testing
- ✅ **Scalable**: Handles growth efficiently

### For Business
- ✅ **Reliable**: Automated process reduces errors
- ✅ **Trackable**: Full visibility into operations
- ✅ **Efficient**: Processes all centers automatically
- ✅ **Cost Effective**: Runs during off-peak hours

---

## Next Steps

1. **Configure APIs**: Set `LOCATION_SLUG_API_URL` and `LOCATION_DATA_API_URL`
2. **Set Schedule**: Configure `CRON_SCHEDULE` as needed
3. **Test Manually**: Use manual endpoints to verify
4. **Monitor First Run**: Check logs and database after first automated run
5. **Adjust as Needed**: Fine-tune schedule and error handling

---

## Questions & Support

For questions or issues:
- Check logs: Application logs show detailed execution flow
- Review database: Check `centers` and `batch_runs` tables
- Use status endpoints: Monitor via `/cron/status` and `/events/status/{run_id}`
- Manual testing: Use manual endpoints to debug

---

**Document Version**: 1.0  
**Last Updated**: 2024-01-15

