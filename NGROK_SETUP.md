# Ngrok Setup Guide for CN Chatbot

This guide will help you run your FastAPI chatbot locally and expose it to the internet using ngrok.

## What is Ngrok?

Ngrok creates a secure tunnel to your localhost, allowing you to:
- Share your local API with others
- Test webhooks
- Access your local server from anywhere
- Get a public HTTPS URL for your local app

## Prerequisites

1. **Python 3.11+** - Already have this
2. **Ngrok** - Need to install (see below)
3. **Project dependencies** - Will be installed automatically

## Step 1: Install Ngrok

### Option A: Download from Website (Recommended)

1. Go to [ngrok.com/download](https://ngrok.com/download)
2. Download for Windows
3. Extract `ngrok.exe` to a folder in your PATH, or:
   - `C:\Program Files\ngrok\` (requires admin)
   - Or any folder and add it to PATH

### Option B: Install via Package Manager

**Using winget (Windows 10/11):**
```powershell
winget install ngrok
```

**Using Chocolatey:**
```powershell
choco install ngrok
```

### Option C: Install via npm (if you have Node.js)
```bash
npm install -g ngrok
```

### Verify Installation

Open a new terminal and run:
```bash
ngrok version
```

You should see the ngrok version number.

## Step 2: Sign Up for Free Ngrok Account (Optional but Recommended)

1. Go to [ngrok.com/signup](https://ngrok.com/signup)
2. Create a free account
3. Get your authtoken from the dashboard
4. Configure ngrok:
   ```bash
   ngrok config add-authtoken YOUR_AUTH_TOKEN
   ```

**Benefits of free account:**
- Custom subdomain (optional)
- Longer session times
- More connections
- Better performance

**Without account:** You can still use ngrok, but with limitations (random URLs, shorter sessions).

## Step 3: Run the Application

### Method 1: Using PowerShell Script (Recommended for Windows)

1. Open PowerShell in the project directory
2. Run:
   ```powershell
   .\start-ngrok.ps1
   ```

The script will:
- Check for Python
- Create/activate virtual environment
- Install dependencies if needed
- Start FastAPI server
- Start ngrok tunnel

### Method 2: Using Batch Script

1. Open Command Prompt in the project directory
2. Run:
   ```cmd
   start-ngrok.bat
   ```

### Method 3: Manual Setup

**Terminal 1 - Start FastAPI:**
```bash
# Activate virtual environment (if exists)
venv\Scripts\activate  # Windows
# or
source venv/bin/activate  # Linux/Mac

# Install dependencies (if not already installed)
pip install -r requirements.txt

# Set environment
set APP_ENV=stage  # Windows CMD
# or
$env:APP_ENV="stage"  # PowerShell
# or
export APP_ENV=stage  # Linux/Mac

# Start FastAPI
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

**Terminal 2 - Start ngrok:**
```bash
ngrok http 8000
```

## Step 4: Access Your Application

After starting ngrok, you'll see output like:

```
Forwarding  https://abc123.ngrok-free.app -> http://localhost:8000
```

### URLs Available:

1. **Public HTTPS URL (from ngrok):**
   - `https://abc123.ngrok-free.app`
   - This is accessible from anywhere on the internet

2. **Local URL:**
   - `http://localhost:8000`
   - Only accessible on your machine

3. **API Documentation:**
   - `https://abc123.ngrok-free.app/docs` (Swagger UI)
   - `https://abc123.ngrok-free.app/redoc` (ReDoc)

## Step 5: Test Your API

### Using curl:
```bash
# Health check
curl https://abc123.ngrok-free.app/health

# FAQ endpoint
curl -X POST "https://abc123.ngrok-free.app/faq/" \
  -H "Content-Type: application/json" \
  -d "{\"question\": \"What is your return policy?\"}"
```

### Using the API Docs:
1. Go to: `https://abc123.ngrok-free.app/docs`
2. Try the `/faq/` endpoint
3. Enter a question and click "Execute"

## Ngrok Dashboard (If you have an account)

If you signed up for ngrok:
1. Go to [dashboard.ngrok.com](https://dashboard.ngrok.com)
2. See all your active tunnels
3. View request logs
4. Monitor traffic

## Troubleshooting

### Error: "ngrok not found"

**Solution:**
1. Install ngrok (see Step 1)
2. Add ngrok to your PATH
3. Or use full path: `C:\path\to\ngrok.exe http 8000`

### Error: "Port 8000 already in use"

**Solution:**
1. Find what's using port 8000:
   ```powershell
   netstat -ano | findstr :8000
   ```
2. Kill the process or use a different port:
   ```bash
   uvicorn app.main:app --reload --host 0.0.0.0 --port 8001
   ngrok http 8001
   ```

### Error: "Module not found"

**Solution:**
1. Activate virtual environment
2. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```

### Ngrok URL changes every time

**Solution:**
1. Sign up for free ngrok account
2. Get authtoken and configure:
   ```bash
   ngrok config add-authtoken YOUR_TOKEN
   ```
3. Use reserved domain (paid feature) or static domain (free with account)

### "ngrok session expired"

**Solution:**
- Free ngrok sessions expire after some time
- Just restart ngrok: `ngrok http 8000`
- Or sign up for account for longer sessions

## Advanced Ngrok Configuration

### Custom Configuration File

Create `ngrok.yml`:

```yaml
version: "2"
authtoken: YOUR_AUTH_TOKEN
tunnels:
  chatbot:
    addr: 8000
    proto: http
    bind_tls: true
```

Run with:
```bash
ngrok start chatbot
```

### Inspect Requests

Ngrok provides a web interface to inspect requests:

1. Start ngrok: `ngrok http 8000`
2. Open: `http://127.0.0.1:4040` in your browser
3. See all requests, responses, and replay them

## Security Notes

⚠️ **Important:**
- Your local server is now accessible on the internet
- Anyone with the ngrok URL can access it
- Don't expose sensitive data
- Use HTTPS (ngrok provides this automatically)
- Consider adding authentication for production use

## Stopping the Services

1. **Stop ngrok:** Press `Ctrl+C` in the ngrok terminal
2. **Stop FastAPI:** Press `Ctrl+C` in the FastAPI terminal
3. **Or use scripts:** The scripts handle cleanup automatically

## Next Steps

1. ✅ Install ngrok
2. ✅ Run the application
3. ✅ Test the API endpoints
4. ✅ Share the ngrok URL with others
5. ✅ Monitor requests in ngrok dashboard

## Useful Commands

```bash
# Start ngrok with specific port
ngrok http 8000

# Start ngrok with custom subdomain (requires account)
ngrok http 8000 --subdomain=my-chatbot

# View ngrok web interface
# Open: http://127.0.0.1:4040

# Check ngrok status
ngrok status

# List all tunnels
ngrok api tunnels list
```

---

**Your ngrok URL will look like:** `https://abc123.ngrok-free.app`

Replace `abc123` with your actual ngrok subdomain.

