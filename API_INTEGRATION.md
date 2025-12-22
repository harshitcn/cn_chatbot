# API Integration for Tier 3

## Overview
Tier 3 now uses API-based data extraction instead of web scraping. The system follows this flow:
1. **TIER 1**: Predefined Q&A (exact matching)
2. **TIER 2**: FAQ data (exact + semantic search)
3. **TIER 3**: API calls based on query keywords

## API Endpoints

### Base URL
```
https://services.codeninjas.com/api/v1
```

### Available Endpoints

1. **Facility Information**
   - `GET /facility/[facility-slug]`
   - Returns facility data including facilityGUID

2. **Facility Profile**
   - `GET /facility/profile/slug/[facility-slug]`
   - Returns facility profile data

3. **Upcoming Camps**
   - `GET /facility/camps/upcoming/[facilityGUID]`
   - Returns list of upcoming camps

4. **Camps by Week**
   - `GET /facility/camps/[facilityGUID]/byweek/[Year]/[Week Number]`
   - Returns camps for a specific week/year

## Query Intent Detection

The system automatically detects user intent from query keywords:

- **Camps**: Keywords like "camp", "camps", "upcoming camp", "camp schedule"
- **Events**: Keywords like "event", "events", "upcoming event"
- **Clubs**: Keywords like "club", "clubs"
- **Programs**: Keywords like "program", "programs", "create", "academy"
- **Facility**: Keywords like "facility", "location", "address", "contact", "info"

## How It Works

1. User asks a question with location
2. System checks predefined Q&A → FAQ data → API (based on keywords)
3. For camp queries, system calls camp API
4. For event queries, system calls event API (or checks facility data)
5. Facility GUID is automatically fetched from location API

## Configuration

API endpoints can be configured in `app/config.py`:
- `data_api_base_url`: Base URL for APIs (default: `https://services.codeninjas.com/api/v1`)
- `data_api_key`: Optional API key for authentication

## Files

- `app/utils/data_api_client.py`: API client for fetching data
- `app/utils/api_query_engine.py`: Query engine that processes API responses
- `app/chains.py`: Updated to use API instead of scraping

