# Code Ninjas Events Discovery Module - Documentation

## Table of Contents
1. [Overview](#overview)
2. [Architecture](#architecture)
3. [API Endpoints](#api-endpoints)
4. [Component Details](#component-details)
5. [Data Flow](#data-flow)
6. [Configuration](#configuration)
7. [Usage Examples](#usage-examples)
8. [Error Handling](#error-handling)
9. [Troubleshooting](#troubleshooting)

---

## Overview

The Events Discovery Module is an automated system that uses AI (LLM) to search for and compile lists of family-friendly local events near Code Ninjas centers. The system generates CSV reports that can be distributed to franchisees monthly, helping them identify community engagement opportunities.

### Key Features
- **Automated Event Discovery**: Uses LLM (Grok/OpenAI) to search for local events
- **Batch Processing**: Process multiple centers in parallel
- **CSV Generation**: Creates structured CSV files with event data
- **Email Distribution**: Optional automated email delivery
- **Status Tracking**: Monitor batch runs in real-time
- **International Support**: Works with US, Canada, UK, and other countries

---

## Architecture

### Component Structure

```
app/
├── routes/
│   └── events.py          # FastAPI endpoints
├── utils/
│   ├── llm_client.py      # LLM API integration
│   ├── event_parser.py    # Parse AI responses
│   ├── csv_generator.py   # Generate CSV files
│   ├── email_service.py   # Email distribution
│   └── event_scheduler.py # Batch processing
├── models.py              # Pydantic models
├── config.py              # Configuration settings
└── prompts/
    └── events_discovery_prompt.txt  # AI prompt template
```

### Data Flow

```
1. API Request → FastAPI Router
2. Router → LLM Client (generates prompt, calls LLM API)
3. LLM Response → Event Parser (extracts structured data)
4. Parsed Events → CSV Generator (creates CSV file)
5. CSV File → Email Service (optional distribution)
6. Results → Response to client
```

---

## API Endpoints

### 1. POST `/events/discover`

**Purpose**: Discover events for a single Code Ninjas center.

**Request Body**:
```json
{
  "center_id": "CN001",
  "center_name": "Code Ninjas Plano",
  "zip_code": "75093",
  "city": "Plano",
  "state": "TX",
  "country": "USA",
  "radius": 5
}
```

**Parameters**:
- `center_id` (required): Unique identifier for the center
- `center_name` (required): Name of the Code Ninjas center
- `zip_code` (optional): ZIP or postal code
- `city` (optional): City name
- `state` (optional): State or province
- `country` (optional, default: "USA"): Country name
- `radius` (optional, default: 5): Search radius in miles (1-50)

**Response**:
```json
{
  "center_id": "CN001",
  "center_name": "Code Ninjas Plano",
  "events": [
    {
      "event_name": "Plano Community Festival",
      "event_date": "2024-03-15",
      "website_url": "https://example.com/festival",
      "location": "Plano Community Center",
      "organizer_contact": "events@plano.gov",
      "fees": "Free",
      "notes": "Family-friendly event with activities for kids"
    }
  ],
  "event_count": 15,
  "csv_path": "data/events/2024-12-22/Events_Code_Ninjas_Plano_2024-12-22.csv",
  "status": "success",
  "message": "Successfully found 15 events",
  "generated_at": "2024-12-22T10:30:00"
}
```

**How It Works**:
1. Receives center information (location, radius, etc.)
2. Generates AI prompt using the template with location substitution
3. Calls LLM API (Grok/OpenAI) with the prompt
4. Parses AI response to extract event data
5. Generates CSV file with events and disclaimer
6. Returns structured response with events and CSV path

**Status Values**:
- `success`: Events found and parsed successfully
- `partial`: Some events found but parsing had issues
- `failed`: No events found or error occurred

---

### 2. POST `/events/batch`

**Purpose**: Start a batch event discovery run for multiple centers.

**Request Body**:
```json
{
  "centers": [
    {
      "center_id": "CN001",
      "center_name": "Code Ninjas Plano",
      "zip_code": "75093",
      "city": "Plano",
      "state": "TX",
      "country": "USA",
      "radius": 5,
      "owner_email": "owner@plano.codeninjas.com"
    },
    {
      "center_id": "CN002",
      "center_name": "Code Ninjas Austin",
      "zip_code": "78759",
      "city": "Austin",
      "state": "TX",
      "country": "USA",
      "radius": 10,
      "owner_email": "owner@austin.codeninjas.com"
    }
  ],
  "send_emails": false
}
```

**Parameters**:
- `centers` (required): Array of center information objects
- `send_emails` (optional, default: false): Whether to send email notifications

**Response**:
```json
{
  "run_id": "550e8400-e29b-41d4-a716-446655440000",
  "status": "running",
  "message": "Batch run started for 2 centers",
  "started_at": "2024-12-22T10:30:00"
}
```

**How It Works**:
1. Creates a batch run with unique ID
2. Starts background task to process centers in parallel
3. Returns immediately with run ID for status tracking
4. Processes up to 5 centers concurrently (configurable)
5. Updates run status as each center completes
6. Optionally sends emails when `send_emails` is true

**Background Processing**:
- Centers are processed asynchronously in parallel
- Maximum 5 concurrent requests (to avoid rate limiting)
- Each center discovery follows the same flow as single discovery
- Results are tracked and aggregated in the batch run status

---

### 3. GET `/events/status/{run_id}`

**Purpose**: Get the current status of a batch run.

**Path Parameters**:
- `run_id` (required): The batch run ID returned from POST `/events/batch`

**Response** (Running):
```json
{
  "run_id": "550e8400-e29b-41d4-a716-446655440000",
  "status": "running",
  "total_centers": 10,
  "processed_centers": 7,
  "successful_centers": 6,
  "failed_centers": 1,
  "started_at": "2024-12-22T10:30:00",
  "completed_at": null,
  "errors": [
    "Center CN005: LLM API returned empty response"
  ],
  "results": [
    {
      "center_id": "CN001",
      "center_name": "Code Ninjas Plano",
      "events": [...],
      "event_count": 15,
      "csv_path": "data/events/2024-12-22/Events_Code_Ninjas_Plano_2024-12-22.csv",
      "status": "success",
      "message": "Successfully found 15 events",
      "generated_at": "2024-12-22T10:30:15"
    }
  ]
}
```

**Response** (Completed):
```json
{
  "run_id": "550e8400-e29b-41d4-a716-446655440000",
  "status": "completed",
  "total_centers": 10,
  "processed_centers": 10,
  "successful_centers": 9,
  "failed_centers": 1,
  "started_at": "2024-12-22T10:30:00",
  "completed_at": "2024-12-22T10:35:00",
  "errors": [...],
  "results": [...]
}
```

**Status Values**:
- `running`: Batch run is in progress
- `completed`: All centers have been processed
- `failed`: Batch run encountered a fatal error

**How It Works**:
1. Looks up batch run by ID in active or completed runs
2. Returns current status with progress metrics
3. Includes individual center results as they complete
4. Provides error messages for failed centers

---

## Component Details

### LLM Client (`app/utils/llm_client.py`)

**Purpose**: Handles communication with LLM APIs (Grok, OpenAI, etc.)

**Key Features**:
- Supports multiple LLM providers (Grok, OpenAI)
- Automatic retry logic (3 attempts)
- Timeout handling (60 seconds)
- Configurable model selection

**Methods**:
- `generate_events_prompt(location, radius, country)`: Loads template and substitutes values
- `query_llm(prompt)`: Sends prompt to LLM API with retry logic

**How It Works**:
1. Loads prompt template from `app/prompts/events_discovery_prompt.txt`
2. Replaces placeholders: `{{ZIP code}}`, `{{radius}}`, `{{country}}`
3. Builds API request payload based on provider
4. Sends request with proper headers and authentication
5. Handles retries on failures (network errors, timeouts)
6. Extracts text response from API JSON response

**Error Handling**:
- Retries on timeouts and 5xx errors
- Fails immediately on 4xx errors (client errors)
- Returns None if all retries fail

---

### Event Parser (`app/utils/event_parser.py`)

**Purpose**: Extracts structured event data from LLM text responses

**Key Features**:
- Handles multiple table formats (markdown, plaintext)
- Flexible parsing for incomplete data
- Handles missing fields gracefully

**Methods**:
- `parse_ai_response(response)`: Main parsing method

**How It Works**:
1. Attempts to detect table format (markdown vs plaintext)
2. Extracts table rows and headers
3. Maps columns to event fields:
   - Event Name → `event_name`
   - Event Date → `event_date`
   - Website/URL → `website_url`
   - Location → `location`
   - Contact → `organizer_contact`
   - Fees → `fees`
   - Notes → `notes`
4. Creates `EventItem` objects for each row
5. Falls back to pattern matching if no table found

**Supported Formats**:
- Markdown tables: `| Column1 | Column2 |`
- Plaintext tables: Tab-separated or space-separated
- Key-value pairs: `Event: Name`, `Date: 2024-03-15`

---

### CSV Generator (`app/utils/csv_generator.py`)

**Purpose**: Generates CSV files from event data

**Key Features**:
- UTF-8 encoding with BOM (Excel compatible)
- Automatic date-based directory organization
- Includes disclaimer at bottom
- Handles special characters in filenames

**Methods**:
- `generate_csv(events, center_name, output_path)`: Creates CSV file
- `generate_fallback_csv(center_name, message)`: Creates CSV when no events found

**How It Works**:
1. Creates date-based directory: `data/events/YYYY-MM-DD/`
2. Generates filename: `Events_{CenterName}_{YYYY-MM-DD}.csv`
3. Writes CSV with headers:
   - Event Name
   - Event Date
   - Event Website / URL
   - Location
   - Organizer Contact Information
   - Fees (if any)
   - Notes
4. Writes event rows
5. Appends disclaimer text
6. Returns file path

**File Structure**:
```
data/events/
└── 2024-12-22/
    ├── Events_Code_Ninjas_Plano_2024-12-22.csv
    └── Events_Code_Ninjas_Austin_2024-12-22.csv
```

---

### Email Service (`app/utils/email_service.py`)

**Purpose**: Sends event discovery reports via email

**Key Features**:
- SMTP support with TLS
- Batch email sending
- Attaches CSV files
- Configurable from address

**Methods**:
- `send_events_report(...)`: Send single report
- `send_batch_reports(reports)`: Send multiple reports

**How It Works**:
1. Checks if email is configured (SMTP settings)
2. Creates email message with:
   - Subject: "Code Ninjas {CenterName} - Local Events Report"
   - Body: Summary with event count and location
   - Attachment: CSV file
3. Connects to SMTP server
4. Sends email to center owner (if email provided)

**Email Body Example**:
```
Hello Code Ninjas Plano Team,

Your monthly local events discovery report is ready!

Summary:
- Center: Code Ninjas Plano
- Location: Plano, TX
- Search Radius: 5 miles
- Events Found: 15

[CSV file attached]
```

**Configuration Required**:
- `EMAIL_SMTP_HOST`: SMTP server address
- `EMAIL_SMTP_PORT`: SMTP port (usually 587)
- `EMAIL_SMTP_USER`: SMTP username
- `EMAIL_SMTP_PASSWORD`: SMTP password
- `EMAIL_FROM`: From email address

---

### Event Scheduler (`app/utils/event_scheduler.py`)

**Purpose**: Manages batch runs and parallel processing

**Key Features**:
- Tracks batch run status
- Parallel processing with concurrency control
- Error aggregation
- Run history

**Methods**:
- `create_batch_run(total_centers)`: Create new batch run
- `get_run_status(run_id)`: Get current status
- `update_run_status(run_id, result, error)`: Update with result
- `process_batch_async(centers, discovery_func, max_concurrent)`: Process in parallel

**How It Works**:
1. Creates batch run with unique UUID
2. Tracks run in `active_runs` dictionary
3. Processes centers with semaphore (max 5 concurrent)
4. Updates status as each center completes
5. Moves to `completed_runs` when done
6. Aggregates errors and results

**Concurrency Control**:
- Uses `asyncio.Semaphore` to limit concurrent requests
- Default: 5 concurrent centers
- Prevents API rate limiting
- Handles exceptions gracefully

---

## Data Flow

### Single Center Discovery Flow

```
1. Client → POST /events/discover
   ↓
2. Router validates request (Pydantic model)
   ↓
3. Router → discover_events_for_center()
   ↓
4. Build location string from center info
   ↓
5. LLM Client → generate_events_prompt()
   - Loads template
   - Substitutes {{location}}, {{radius}}, {{country}}
   ↓
6. LLM Client → query_llm(prompt)
   - Sends to Grok/OpenAI API
   - Retries on failure (3 attempts)
   ↓
7. Event Parser → parse_ai_response()
   - Detects table format
   - Extracts event rows
   - Creates EventItem objects
   ↓
8. CSV Generator → generate_csv()
   - Creates date directory
   - Writes CSV with events
   - Adds disclaimer
   ↓
9. Router → EventDiscoveryResponse
   - Returns events, CSV path, status
   ↓
10. Client receives response
```

### Batch Processing Flow

```
1. Client → POST /events/batch
   ↓
2. Router creates batch run (UUID)
   ↓
3. Router starts background task
   ↓
4. Router returns run_id immediately
   ↓
5. Background task processes centers:
   - Creates semaphore (max 5 concurrent)
   - For each center:
     * Calls discover_events_for_center()
     * Updates run status
   ↓
6. If send_emails=true:
   - Email Service sends reports
   ↓
7. Batch run marked as "completed"
   ↓
8. Client polls GET /events/status/{run_id}
   - Gets progress updates
   - Receives final results
```

---

## Configuration

### Environment Variables

Add to your `.env` file:

```env
# LLM API Configuration (Required)
LLM_API_KEY=your_grok_or_openai_api_key
LLM_API_URL=https://api.x.ai/v1/chat/completions
LLM_PROVIDER=grok  # or 'openai'
LLM_MODEL=grok-beta  # or 'gpt-4', 'gpt-3.5-turbo', etc.

# Email Configuration (Optional)
EMAIL_SMTP_HOST=smtp.gmail.com
EMAIL_SMTP_PORT=587
EMAIL_SMTP_USER=your_email@gmail.com
EMAIL_SMTP_PASSWORD=your_app_password
EMAIL_FROM=noreply@codeninjas.com
EMAIL_USE_TLS=true

# Events Storage (Optional - defaults shown)
EVENTS_STORAGE_PATH=data/events
DEFAULT_SEARCH_RADIUS=5
```

### LLM Provider Setup

**Grok (xAI)**:
```env
LLM_PROVIDER=grok
LLM_API_URL=https://api.x.ai/v1/chat/completions
LLM_MODEL=grok-beta
LLM_API_KEY=xai-...
```

**OpenAI**:
```env
LLM_PROVIDER=openai
LLM_API_URL=https://api.openai.com/v1/chat/completions
LLM_MODEL=gpt-4
LLM_API_KEY=sk-...
```

**Custom Provider**:
- Must support OpenAI-compatible API format
- Response must include `choices[0].message.content`

---

## Usage Examples

### Example 1: Single Center Discovery

```bash
curl -X POST "http://localhost:8000/events/discover" \
  -H "Content-Type: application/json" \
  -d '{
    "center_id": "CN001",
    "center_name": "Code Ninjas Plano",
    "zip_code": "75093",
    "city": "Plano",
    "state": "TX",
    "country": "USA",
    "radius": 5
  }'
```

**Response**:
```json
{
  "center_id": "CN001",
  "center_name": "Code Ninjas Plano",
  "events": [
    {
      "event_name": "Plano Community Festival",
      "event_date": "March 15, 2024",
      "website_url": "https://plano.gov/festival",
      "location": "Plano Community Center",
      "organizer_contact": "events@plano.gov",
      "fees": "Free",
      "notes": "Family-friendly event"
    }
  ],
  "event_count": 15,
  "csv_path": "data/events/2024-12-22/Events_Code_Ninjas_Plano_2024-12-22.csv",
  "status": "success",
  "message": "Successfully found 15 events",
  "generated_at": "2024-12-22T10:30:00"
}
```

### Example 2: Batch Processing

```bash
curl -X POST "http://localhost:8000/events/batch" \
  -H "Content-Type: application/json" \
  -d '{
    "centers": [
      {
        "center_id": "CN001",
        "center_name": "Code Ninjas Plano",
        "zip_code": "75093",
        "city": "Plano",
        "state": "TX",
        "country": "USA",
        "radius": 5,
        "owner_email": "owner@plano.codeninjas.com"
      },
      {
        "center_id": "CN002",
        "center_name": "Code Ninjas Austin",
        "zip_code": "78759",
        "city": "Austin",
        "state": "TX",
        "country": "USA",
        "radius": 10
      }
    ],
    "send_emails": true
  }'
```

**Response**:
```json
{
  "run_id": "550e8400-e29b-41d4-a716-446655440000",
  "status": "running",
  "message": "Batch run started for 2 centers",
  "started_at": "2024-12-22T10:30:00"
}
```

### Example 3: Check Batch Status

```bash
curl "http://localhost:8000/events/status/550e8400-e29b-41d4-a716-446655440000"
```

**Response** (while running):
```json
{
  "run_id": "550e8400-e29b-41d4-a716-446655440000",
  "status": "running",
  "total_centers": 2,
  "processed_centers": 1,
  "successful_centers": 1,
  "failed_centers": 0,
  "started_at": "2024-12-22T10:30:00",
  "completed_at": null,
  "errors": [],
  "results": [...]
}
```

### Example 4: Python Client

```python
import httpx
import asyncio

async def discover_events():
    async with httpx.AsyncClient() as client:
        # Single discovery
        response = await client.post(
            "http://localhost:8000/events/discover",
            json={
                "center_id": "CN001",
                "center_name": "Code Ninjas Plano",
                "zip_code": "75093",
                "city": "Plano",
                "state": "TX",
                "country": "USA",
                "radius": 5
            }
        )
        result = response.json()
        print(f"Found {result['event_count']} events")
        print(f"CSV: {result['csv_path']}")

asyncio.run(discover_events())
```

---

## Error Handling

### Error Types

1. **LLM API Errors**:
   - Timeout: Retries 3 times
   - Rate Limit: Retries with backoff
   - Invalid API Key: Fails immediately
   - Empty Response: Returns fallback CSV

2. **Parsing Errors**:
   - No table found: Attempts pattern matching
   - Invalid format: Skips problematic rows
   - Missing fields: Uses None/empty string

3. **File System Errors**:
   - Directory creation: Auto-creates if missing
   - Permission errors: Logs and raises exception
   - Disk full: Raises exception

4. **Email Errors**:
   - SMTP connection failure: Logs and continues
   - Invalid recipient: Skips and logs
   - Attachment error: Logs and continues

### Error Response Format

```json
{
  "detail": "Error message here"
}
```

**HTTP Status Codes**:
- `200`: Success
- `400`: Bad request (invalid parameters)
- `404`: Resource not found (batch run ID)
- `500`: Internal server error
- `503`: Service unavailable (memory/rate limit)

### Fallback Behavior

When errors occur:
1. **LLM fails**: Generates CSV with "No events found or AI failed"
2. **Parsing fails**: Includes events that were successfully parsed
3. **CSV generation fails**: Returns error in response, no CSV path
4. **Email fails**: Logs error, continues processing other centers

---

## Troubleshooting

### Common Issues

**1. "LLM API key not configured"**
- **Solution**: Add `LLM_API_KEY` to `.env` file
- **Check**: Verify API key is valid and has credits

**2. "LLM API returned empty response"**
- **Solution**: Check API endpoint URL and model name
- **Check**: Verify API key has access to the model
- **Check**: Review API logs for errors

**3. "No events parsed from LLM response"**
- **Solution**: LLM may not have returned table format
- **Check**: Review raw LLM response in logs
- **Solution**: Try adjusting prompt template

**4. "Email service not configured"**
- **Solution**: Add email settings to `.env` or set `send_emails=false`
- **Note**: Email is optional, CSV files are still generated

**5. "Batch run not found"**
- **Solution**: Batch runs are stored in memory (lost on restart)
- **Note**: For production, consider persistent storage

**6. "CSV file not found"**
- **Solution**: Check `EVENTS_STORAGE_PATH` setting
- **Check**: Verify file system permissions
- **Check**: Look in `data/events/YYYY-MM-DD/` directory

### Debugging Tips

1. **Enable Debug Logging**:
   ```env
   DEBUG=true
   ```

2. **Check Logs**:
   - All components use Python `logging` module
   - Look for ERROR and WARNING messages
   - Check LLM API response in logs

3. **Test LLM Connection**:
   ```python
   from app.utils.llm_client import LLMClient
   client = LLMClient()
   response = await client.query_llm("Test prompt")
   print(response)
   ```

4. **Verify CSV Generation**:
   ```python
   from app.utils.csv_generator import CSVGenerator
   from app.models import EventItem
   
   generator = CSVGenerator()
   events = [EventItem(event_name="Test", event_date="2024-01-01")]
   path = generator.generate_csv(events, "Test Center")
   print(f"CSV created at: {path}")
   ```

---

## Best Practices

1. **Batch Processing**:
   - Process centers in batches of 10-20 for optimal performance
   - Monitor batch status regularly
   - Set appropriate `max_concurrent` based on API rate limits

2. **Error Handling**:
   - Always check `status` field in responses
   - Handle `failed` and `partial` statuses appropriately
   - Log errors for debugging

3. **CSV Files**:
   - CSV files are organized by date automatically
   - Keep old files for historical reference
   - Consider archiving after distribution

4. **Email Distribution**:
   - Test email configuration before batch runs
   - Use `send_emails=false` for testing
   - Verify recipient emails are correct

5. **LLM Usage**:
   - Monitor API usage and costs
   - Adjust `max_tokens` if responses are truncated
   - Consider caching for repeated locations

---

## Future Enhancements

Potential improvements (not currently implemented):

1. **Persistent Storage**: Store batch runs in database
2. **Scheduling**: Integrate APScheduler for monthly automation
3. **Dashboard**: Web UI for monitoring batch runs
4. **Caching**: Cache LLM responses for same locations
5. **Deduplication**: Remove duplicate events across months
6. **Event Scoring**: AI-generated relevance scores
7. **Integration**: Connect with Franchise Dashboard
8. **Notifications**: Slack/Teams notifications for batch completion

---

## Support

For issues or questions:
1. Check logs in application output
2. Review this documentation
3. Verify configuration settings
4. Test individual components
5. Contact development team

---

**Last Updated**: December 2024
**Version**: 1.0.0

