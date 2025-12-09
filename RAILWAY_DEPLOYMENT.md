# Railway.app Deployment Guide

Complete guide to deploy your chatbot on Railway.app (free tier with $5 monthly credit).

## Why Railway?

- ✅ **Always-on** - No spin-down after inactivity
- ✅ **Free $5 credit** monthly (usually enough for small apps)
- ✅ **No forced timeouts** during model loading
- ✅ **Easy GitHub integration**
- ✅ **Automatic deployments**

## Prerequisites

1. **Railway Account** - Sign up at [railway.app](https://railway.app)
2. **GitHub Account** - Your code repository
3. **Credit Card** (optional) - For verification, but won't be charged if you stay within free credits

## Quick Start: Deploy in 5 Minutes

### Step 1: Sign Up for Railway

1. Go to [railway.app](https://railway.app)
2. Click **"Start a New Project"**
3. Sign in with GitHub (recommended)

### Step 2: Create New Project

1. Click **"New Project"**
2. Select **"Deploy from GitHub repo"**
3. Authorize Railway to access your GitHub
4. Select repository: `harshitcn/cn_chatbot`
5. Click **"Deploy Now"**

### Step 3: Configure Environment Variables

Railway will automatically detect Python and start building. While it builds:

1. Go to your project → **Variables** tab
2. Add these environment variables:

   | Variable Name | Value | Required |
   |--------------|-------|----------|
   | `APP_ENV` | `production` | Yes |
   | `PYTHONUNBUFFERED` | `1` | Yes |
   | `DEBUG` | `False` | Recommended |
   | `TOKENIZERS_PARALLELISM` | `false` | Recommended |
   | `OMP_NUM_THREADS` | `1` | Recommended |
   | `MKL_NUM_THREADS` | `1` | Recommended |
   | `HF_HUB_DISABLE_EXPERIMENTAL_WARNING` | `1` | Optional |
   | `TRANSFORMERS_NO_ADVISORY_WARNINGS` | `1` | Optional |
   | `TRANSFORMERS_CACHE` | `/tmp/.cache/huggingface` | Optional |

3. Click **"Add"** for each variable

### Step 4: Configure Service Settings

1. Go to your service → **Settings**
2. **Port:** Railway sets this automatically (don't change)
3. **Health Check Path:** `/health` (optional)
4. **Start Command:** Already set from `Procfile` or `railway.json`

### Step 5: Monitor Deployment

1. Go to **Deployments** tab
2. Watch the build logs
3. First deployment may take 5-10 minutes (downloading dependencies and models)
4. Once deployed, Railway will provide a URL like: `https://your-app-name.up.railway.app`

## Configuration Files

Railway uses these files (already created):

- **`Procfile`** - Defines the start command
- **`railway.json`** - Advanced Railway configuration
- **`requirements.txt`** - Python dependencies (auto-detected)

## Environment Variables Explained

### Required Variables:

- **`APP_ENV=production`** - Sets the application environment
- **`PYTHONUNBUFFERED=1`** - Ensures logs are visible in real-time

### Memory Optimization Variables:

- **`TOKENIZERS_PARALLELISM=false`** - Prevents tokenizer warnings and reduces memory
- **`OMP_NUM_THREADS=1`** - Limits OpenMP threads (memory optimization)
- **`MKL_NUM_THREADS=1`** - Limits MKL threads (memory optimization)

### Optional Variables:

- **`TRANSFORMERS_CACHE`** - Cache location for HuggingFace models
- **`HF_HUB_DISABLE_EXPERIMENTAL_WARNING=1`** - Reduces log noise
- **`TRANSFORMERS_NO_ADVISORY_WARNINGS=1`** - Reduces log noise

## Free Tier Limits

Railway's free tier includes:

- **$5 monthly credit** - Usually enough for a small app running 24/7
- **512MB-1GB RAM** - Depends on plan
- **No forced spin-down** - Service stays awake
- **Unlimited deployments** - Deploy as often as you want
- **Custom domains** - Free SSL certificates

### Monitoring Usage:

1. Go to **Settings** → **Usage**
2. Monitor your monthly credit usage
3. If you exceed $5, you'll need to add payment method (but won't be charged if you upgrade plan)

## Advantages Over Other Free Tiers

| Feature | Railway | Render Free | Azure F1 |
|---------|---------|-------------|----------|
| Always-on | ✅ Yes | ❌ Spins down | ⚠️ May spin down |
| Model loading timeout | ✅ No limit | ❌ 30-60s timeout | ⚠️ May timeout |
| Free credits | ✅ $5/month | ✅ Unlimited | ✅ Free |
| Memory | 512MB-1GB | 512MB | 1GB |
| Setup complexity | ⭐ Easy | ⭐⭐ Medium | ⭐⭐⭐ Complex |

## Troubleshooting

### Build Fails

**Error:** "Module not found"
- **Solution:** Ensure `requirements.txt` includes all dependencies
- Check build logs for specific missing packages

**Error:** "Out of memory during build"
- **Solution:** Railway may need more resources. Check if you're on free tier limits.

### Deployment Succeeds but App Doesn't Start

**Error:** "Application failed to start"
- **Solution:** 
  1. Check **Logs** tab for error messages
  2. Verify `PORT` environment variable is set (Railway sets this automatically)
  3. Ensure start command in `Procfile` is correct

### Model Loading Takes Too Long

**Issue:** First request times out
- **Solution:**
  1. Increase timeout in `Procfile`: `--timeout-keep-alive 180`
  2. Pre-warm model on startup (if memory allows)
  3. Consider using smaller model

### 502 Bad Gateway on First Request

**Issue:** Request times out during model download
- **Solution:**
  1. Railway doesn't have forced timeouts like Render
  2. Check if it's a memory issue (OOM)
  3. Verify health check isn't triggering during model load
  4. Increase `--timeout-keep-alive` value

## Upgrading to Paid Plan

If you need more resources:

1. Go to **Settings** → **Usage**
2. Click **"Upgrade"**
3. Choose plan:
   - **Developer:** $5/month (1GB RAM, 1 CPU)
   - **Pro:** $20/month (2GB RAM, 2 CPU)

## Custom Domain

Railway provides free custom domains:

1. Go to **Settings** → **Domains**
2. Click **"Generate Domain"** or **"Custom Domain"**
3. Follow instructions to configure DNS

## Continuous Deployment

Railway automatically deploys on every push to your main branch:

1. Push to GitHub: `git push origin main`
2. Railway detects changes
3. Automatically builds and deploys
4. You'll see new deployment in **Deployments** tab

## Monitoring and Logs

### View Logs:

1. Go to your service
2. Click **"View Logs"** or **"Logs"** tab
3. Real-time logs are available
4. Search and filter logs

### Metrics:

1. Go to **Metrics** tab
2. View:
   - CPU usage
   - Memory usage
   - Request count
   - Response times

## Cost Optimization Tips

1. **Monitor usage** - Check usage dashboard regularly
2. **Optimize memory** - Use memory optimization variables
3. **Use smaller models** - Reduces memory and startup time
4. **Lazy loading** - Load models on first request (already implemented)

## Comparison with Other Platforms

### Railway vs Render:

| Feature | Railway | Render |
|---------|---------|--------|
| Free tier | $5 credit/month | Unlimited (spins down) |
| Always-on | ✅ Yes | ❌ No |
| Setup | ⭐ Easy | ⭐⭐ Medium |
| Timeouts | ✅ Flexible | ❌ 30-60s limit |

### Railway vs Azure:

| Feature | Railway | Azure F1 |
|---------|---------|----------|
| Free tier | $5 credit/month | Free (limited) |
| Always-on | ✅ Yes | ⚠️ May spin down |
| Setup | ⭐ Easy | ⭐⭐⭐ Complex |
| Deployment | ⭐ GitHub integration | ⭐⭐⭐ Multiple options |

## Next Steps

1. ✅ Deploy to Railway
2. ✅ Configure environment variables
3. ✅ Test the API: `https://your-app.up.railway.app/health`
4. ✅ Monitor usage and logs
5. ✅ Set up custom domain (optional)

## Support

- **Railway Docs:** https://docs.railway.app
- **Railway Discord:** https://discord.gg/railway
- **Railway Status:** https://status.railway.app

---

**Your Railway URL will be:** `https://your-app-name.up.railway.app`

Replace `your-app-name` with your actual Railway project name.

