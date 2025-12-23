# Events Discovery Module - Quick Setup Guide

## Configuration Required

The Events Discovery Module requires LLM API configuration to function. You're seeing this error because the API key and URL are not configured.

## Step 1: Create `.env` File

Create a `.env` file in the project root (copy from `.env.example`):

```bash
# Windows
copy .env.example .env

# Linux/Mac
cp .env.example .env
```

## Step 2: Configure LLM API

You need to choose one LLM provider and configure it:

### Option A: Grok (xAI) - Recommended

1. Get your API key from [xAI Console](https://console.x.ai/)
2. Add to `.env`:

```env
LLM_API_KEY=xai-your_api_key_here
LLM_API_URL=https://api.x.ai/v1/chat/completions
LLM_PROVIDER=grok
LLM_MODEL=grok-beta
```

### Option B: OpenAI

1. Get your API key from [OpenAI Platform](https://platform.openai.com/api-keys)
2. Add to `.env`:

```env
LLM_API_KEY=sk-your_openai_api_key_here
LLM_API_URL=https://api.openai.com/v1/chat/completions
LLM_PROVIDER=openai
LLM_MODEL=gpt-4
```

**Note**: You can also use `gpt-3.5-turbo` for cost savings, though results may vary.

### Option C: Other OpenAI-Compatible APIs

If you're using a different provider (Anthropic, Mistral, etc.), configure it with their endpoint:

```env
LLM_API_KEY=your_api_key
LLM_API_URL=https://api.provider.com/v1/chat/completions
LLM_PROVIDER=openai
LLM_MODEL=model-name
```

**Note**: The API must support OpenAI-compatible format with response structure:
```json
{
  "choices": [{
    "message": {
      "content": "response text"
    }
  }]
}
```

## Step 3: Verify Configuration

After creating `.env`, restart your FastAPI application:

```bash
# If running with uvicorn
uvicorn app.main:app --reload

# Or however you're running the app
```

## Step 4: Test the Configuration

Make a test request to verify it's working:

```bash
curl -X POST "http://localhost:8000/events/discover" \
  -H "Content-Type: application/json" \
  -d '{
    "center_id": "TEST001",
    "center_name": "Test Center",
    "zip_code": "75093",
    "city": "Plano",
    "state": "TX",
    "country": "USA",
    "radius": 5
  }'
```

## Troubleshooting

### Error: "LLM API key or URL not configured"

**Cause**: The `.env` file doesn't exist or the variables aren't set.

**Solution**:
1. Verify `.env` file exists in project root
2. Check that `LLM_API_KEY` and `LLM_API_URL` are set
3. Make sure there are no extra spaces around the `=` sign
4. Restart the application after changing `.env`

### Error: "401 Unauthorized" or "Invalid API Key"

**Cause**: The API key is incorrect or expired.

**Solution**:
1. Verify your API key is correct (no extra spaces)
2. Check that your API key has credits/quota
3. For Grok: Verify key at https://console.x.ai/
4. For OpenAI: Verify key at https://platform.openai.com/api-keys

### Error: "Connection timeout" or "Connection refused"

**Cause**: The API URL is incorrect or the service is down.

**Solution**:
1. Verify `LLM_API_URL` is correct:
   - Grok: `https://api.x.ai/v1/chat/completions`
   - OpenAI: `https://api.openai.com/v1/chat/completions`
2. Check your internet connection
3. Verify the LLM service status

### Environment-Specific Configuration

The app supports environment-specific `.env` files:

- `.env.stage` - For staging environment (set `APP_ENV=stage`)
- `.env.production` - For production environment (set `APP_ENV=production`)
- `.env` - Default fallback

The app will automatically load the appropriate file based on the `APP_ENV` environment variable.

## Security Notes

⚠️ **Important**: Never commit `.env` files to version control!

1. `.env` should already be in `.gitignore`
2. Use `.env.example` as a template (without real keys)
3. For production, use environment variables or secret management systems
4. Rotate API keys regularly

## Getting API Keys

### Grok (xAI)
1. Visit https://console.x.ai/
2. Sign up or log in
3. Navigate to API Keys
4. Create a new API key
5. Copy and paste into `.env`

### OpenAI
1. Visit https://platform.openai.com/
2. Sign up or log in
3. Go to API Keys section
4. Create a new secret key
5. Copy and paste into `.env`
6. Add payment method if required

## Next Steps

Once configured, you can:
1. Test single center discovery: `POST /events/discover`
2. Run batch processing: `POST /events/batch`
3. Check batch status: `GET /events/status/{run_id}`

See `EVENTS_MODULE_DOCUMENTATION.md` for detailed API documentation.

