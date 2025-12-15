# Three-Tier Chatbot Implementation

## Overview

Your chatbot now implements a three-tier response system:

1. **Tier 1: Predefined Q&A** - Exact/precise matching for predefined questions
2. **Tier 2: FAQ List** - Semantic search through your existing FAQ data
3. **Tier 3: Web Scraping** - Scrapes website for location-specific information when FAQ doesn't have the answer

## Architecture

### Flow Diagram

```
User Question
    ↓
[ Tier 1: Predefined Q&A ]
    ↓ (if no match)
[ Tier 2: FAQ Semantic Search ]
    ↓ (if no match & location detected)
[ Tier 3: Web Scraping ]
    ↓ (if all fail)
Default Response
```

## Files Created/Modified

### New Files

1. **`app/predefined_qa.py`**
   - Contains predefined Q&A matching logic
   - Uses exact and flexible matching strategies
   - Add your predefined questions and answers here

2. **`app/utils/web_scraper.py`**
   - Web scraping utility for location-based queries
   - Uses BeautifulSoup for HTML parsing
   - Configurable URL patterns

### Modified Files

1. **`app/chains.py`**
   - Updated `get_answer()` method to implement three-tier flow
   - Integrated predefined Q&A and web scraping

2. **`app/config.py`**
   - Added web scraping configuration settings:
     - `scrape_base_url`: Base URL for scraping
     - `scrape_url_pattern`: URL pattern template

3. **`requirements.txt`**
   - Added `beautifulsoup4>=4.12.0` for web scraping

## Setup Instructions

### Step 1: Add Predefined Questions and Answers

Edit `app/predefined_qa.py` and add your predefined Q&A pairs to the `PREDEFINED_QA` list:

```python
PREDEFINED_QA: List[Dict[str, str]] = [
    {
        "question": "What is your name?",
        "answer": "I am the Code Ninjas chatbot assistant."
    },
    {
        "question": "How can I contact support?",
        "answer": "You can contact our support team at support@codeninjas.com or call 1-800-CODE-NINJA."
    },
    # Add more predefined Q&A pairs here
]
```

**Matching Strategies:**
- Exact normalized match (case-insensitive, punctuation removed)
- Substring match (user question contains predefined question or vice versa)
- High keyword overlap (≥80% overlap with at least 3 common keywords)

### Step 2: Configure Web Scraping

Set environment variables or add to your `.env` file:

```bash
# Base URL for web scraping
SCRAPE_BASE_URL=https://www.codeninjas.com

# URL pattern (optional, defaults to {base_url}/locations/{location})
# Available placeholders:
#   {base_url} - The base URL
#   {location} - Location slug (lowercase, spaces replaced with hyphens)
#   {location_name} - Original location name
#   {location-slug} - Same as {location}
SCRAPE_URL_PATTERN={base_url}/locations/{location}
```

**Example URL Patterns:**
- `{base_url}/locations/{location}` → `https://example.com/locations/new-york`
- `{base_url}/{location}` → `https://example.com/new-york`
- `{base_url}/location/{location_name}` → `https://example.com/location/New York`

### Step 3: Test the Implementation

1. **Test Predefined Q&A:**
   ```bash
   curl -X POST http://localhost:8000/faq/ \
     -H "Content-Type: application/json" \
     -d '{"question": "What is your name?"}'
   ```

2. **Test FAQ Search:**
   ```bash
   curl -X POST http://localhost:8000/faq/ \
     -H "Content-Type: application/json" \
     -d '{"question": "What is Code Ninjas?"}'
   ```

3. **Test Web Scraping (with location):**
   ```bash
   curl -X POST http://localhost:8000/faq/ \
     -H "Content-Type: application/json" \
     -d '{"question": "Tell me about Code Ninjas in New York"}'
   ```

## How It Works

### Tier 1: Predefined Q&A

- Checks for exact or very close matches in predefined Q&A list
- Uses multiple matching strategies:
  - Exact normalized match
  - Substring matching
  - High keyword overlap (≥80%)
- Returns immediately if match found

### Tier 2: FAQ Semantic Search

- Uses existing FAISS vector store for semantic search
- Detects location in question
- If location detected, fetches location data from API and merges with FAQ
- Returns best matching answer if similarity score is within threshold

### Tier 3: Web Scraping

- Only triggered if:
  - Location is detected in the question
  - FAQ search didn't return a relevant answer
- Constructs URL based on location name and configured pattern
- Scrapes website content
- Extracts main content (removes scripts, styles, nav, footer, header)
- Returns formatted answer with scraped content

## Configuration Options

### Environment Variables

```bash
# Web Scraping
SCRAPE_BASE_URL=https://www.example.com
SCRAPE_URL_PATTERN={base_url}/locations/{location}

# Location API (existing)
LOCATION_SLUG_API_URL=https://api.example.com/location-slug
LOCATION_DATA_API_URL=https://api.example.com/location-data
LOCATION_API_KEY=your-api-key
```

### URL Pattern Placeholders

- `{base_url}` - Base URL from `SCRAPE_BASE_URL`
- `{location}` - Location slug (lowercase, hyphens)
- `{location_name}` - Original location name
- `{location-slug}` - Same as `{location}`

## Logging

The system logs each tier's execution:

```
INFO: Tier 1: Checking predefined Q&A...
INFO: No match found in predefined Q&A, proceeding to FAQ search...
INFO: Tier 2: Searching FAQ list...
INFO: Location detected: 'New York' in question: 'Tell me about Code Ninjas in New York'
INFO: Tier 3: Attempting to scrape website for location 'New York'...
INFO: Successfully scraped content for location 'New York'
```

## Next Steps

1. **Add your predefined Q&A** to `app/predefined_qa.py`
2. **Configure web scraping** by setting `SCRAPE_BASE_URL` and optionally `SCRAPE_URL_PATTERN`
3. **Test each tier** to ensure they work as expected
4. **Customize matching thresholds** if needed (in `app/predefined_qa.py` and `app/chains.py`)

## Notes

- Predefined Q&A matching is case-insensitive and handles variations
- Web scraping only occurs when a location is detected
- If web scraping fails, the system returns a default response
- All tiers are logged for debugging purposes
- The system gracefully handles errors at each tier

