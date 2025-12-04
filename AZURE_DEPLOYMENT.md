# Azure App Service Deployment Guide (F1 Free Tier)

Complete guide to deploy your chatbot to Azure App Service F1 (Free) plan.

## Prerequisites

1. **Azure Account** - Sign up at [azure.microsoft.com/free](https://azure.microsoft.com/free/)
2. **GitHub Account** - Your code should be in a GitHub repository
3. **Azure CLI** (optional) - For command-line deployment

## Azure F1 Free Tier Specifications

- **Memory:** 1 GB RAM
- **Storage:** 1 GB
- **CPU:** Shared, limited compute
- **Always On:** ❌ Not available (service may spin down after inactivity)
- **Custom Domain:** ❌ Not available on free tier
- **SSL:** ✅ Included

## Step 1: Create Azure Resources

### Option A: Using Azure Portal (Recommended)

1. **Login to Azure Portal:**
   - Go to [portal.azure.com](https://portal.azure.com)
   - Sign in with your Azure account

2. **Create Resource Group:**
   - Click **"Create a resource"** → Search **"Resource group"**
   - Click **"Create"**
   - **Subscription:** Select your subscription
   - **Resource group:** `cn-chatbot-rg`
   - **Region:** Choose closest to you (e.g., `East US`)
   - Click **"Review + create"** → **"Create"**

3. **Create App Service Plan (F1 Free):**
   - Click **"Create a resource"** → Search **"App Service Plan"**
   - Click **"Create"**
   - **Subscription:** Your subscription
   - **Resource Group:** `cn-chatbot-rg`
   - **Name:** `cn-chatbot-plan`
   - **Operating System:** **Linux**
   - **Region:** Same as resource group
   - **Pricing tier:** Click **"Dev/Test"** tab → Select **"F1 Free"**
   - Click **"Review + create"** → **"Create"**
   - Wait for deployment (1-2 minutes)

4. **Create Web App:**
   - Click **"Create a resource"** → Search **"Web App"**
   - Click **"Create"**
   - **Subscription:** Your subscription
   - **Resource Group:** `cn-chatbot-rg`
   - **Name:** `cn-chatbot-app` (must be globally unique, add numbers if needed)
   - **Publish:** **Code**
   - **Runtime stack:** **Python 3.11**
   - **Operating System:** **Linux**
   - **Region:** Same as resource group
   - **App Service Plan:** Select `cn-chatbot-plan`
   - Click **"Review + create"** → **"Create"**
   - Wait for deployment (2-3 minutes)

### Option B: Using Azure CLI

```bash
# Login to Azure
az login

# Create resource group
az group create --name cn-chatbot-rg --location eastus

# Create App Service Plan (F1 Free)
az appservice plan create \
  --name cn-chatbot-plan \
  --resource-group cn-chatbot-rg \
  --sku FREE \
  --is-linux

# Create Web App
az webapp create \
  --name cn-chatbot-app \
  --resource-group cn-chatbot-rg \
  --plan cn-chatbot-plan \
  --runtime "PYTHON:3.11"
```

## Step 2: Configure Azure App Service

### Set Application Settings (Environment Variables)

1. **In Azure Portal:**
   - Go to your Web App → **Configuration** → **Application settings**
   - Click **"+ New application setting"** and add:

   | Name | Value |
   |------|-------|
   | `APP_ENV` | `production` |
   | `PYTHONUNBUFFERED` | `1` |
   | `DEBUG` | `False` |
   | `TOKENIZERS_PARALLELISM` | `false` |
   | `OMP_NUM_THREADS` | `1` |
   | `MKL_NUM_THREADS` | `1` |
   | `HF_HUB_DISABLE_EXPERIMENTAL_WARNING` | `1` |
   | `TRANSFORMERS_NO_ADVISORY_WARNINGS` | `1` |

   - Click **"Save"** at the top

2. **Using Azure CLI:**
```bash
az webapp config appsettings set \
  --name cn-chatbot-app \
  --resource-group cn-chatbot-rg \
  --settings \
    APP_ENV=production \
    PYTHONUNBUFFERED=1 \
    DEBUG=False \
    TOKENIZERS_PARALLELISM=false \
    OMP_NUM_THREADS=1 \
    MKL_NUM_THREADS=1
```

### Configure Startup Command

1. **In Azure Portal:**
   - Go to your Web App → **Configuration** → **General settings**
   - **Startup Command:** Enter:
     ```
     startup.sh
     ```
   - Click **"Save"**

2. **Using Azure CLI:**
```bash
az webapp config set \
  --name cn-chatbot-app \
  --resource-group cn-chatbot-rg \
  --startup-file "startup.sh"
```

## Step 3: Deploy to Azure

### Option A: GitHub Actions (Recommended - Automated)

1. **Get Publish Profile:**
   - Go to your Web App → **Get publish profile**
   - Click **"Download publish profile"**
   - Save the `.PublishSettings` file

2. **Add GitHub Secret:**
   - Go to your GitHub repository → **Settings** → **Secrets and variables** → **Actions**
   - Click **"New repository secret"**
   - **Name:** `AZURE_WEBAPP_PUBLISH_PROFILE`
   - **Value:** Open the downloaded `.PublishSettings` file in a text editor and copy the **entire XML content**
   - Click **"Add secret"**

3. **Update Workflow (if needed):**
   - Edit `.github/workflows/azure-deploy.yml`
   - Update `AZURE_WEBAPP_NAME` to match your app name:
     ```yaml
     env:
       AZURE_WEBAPP_NAME: cn-chatbot-app  # Your actual app name
     ```

4. **Push to GitHub:**
   ```bash
   git add .
   git commit -m "Add Azure deployment configuration"
   git push origin main
   ```

5. **Monitor Deployment:**
   - Go to your GitHub repository → **Actions** tab
   - Watch the deployment workflow run
   - Check Azure Portal → Your Web App → **Deployment Center** for status

### Option B: Manual Deployment (Azure CLI)

```bash
# Install Azure CLI extension for App Service
az extension add --name webapp

# Deploy from local directory
az webapp up \
  --name cn-chatbot-app \
  --resource-group cn-chatbot-rg \
  --runtime "PYTHON:3.11" \
  --startup-file "startup.sh"
```

### Option C: VS Code Azure Extension

1. Install **Azure App Service** extension in VS Code
2. Sign in to Azure
3. Right-click your project → **Deploy to Web App**
4. Select your App Service
5. Wait for deployment

## Step 4: Verify Deployment

1. **Get your app URL:**
   - In Azure Portal → Your Web App → **Overview**
   - Copy the **URL** (e.g., `https://cn-chatbot-app.azurewebsites.net`)

2. **Test the endpoints:**
   ```bash
   # Health check
   curl https://cn-chatbot-app.azurewebsites.net/health

   # Root endpoint
   curl https://cn-chatbot-app.azurewebsites.net/

   # API docs
   # Visit: https://cn-chatbot-app.azurewebsites.net/docs
   ```

3. **Check logs:**
   - In Azure Portal → Your Web App → **Log stream**
   - Or use: `az webapp log tail --name cn-chatbot-app --resource-group cn-chatbot-rg`

## Important Notes for Azure F1 Free Tier

### Limitations

- **No Always On:** Service may spin down after 20 minutes of inactivity
- **Cold Start:** First request after spin-down may take 30-60 seconds
- **Memory Limit:** 1 GB RAM (same as Render, but Azure may be more stable)
- **Compute:** Limited CPU resources
- **Custom Domain:** Not available on free tier

### Memory Optimization

The application is already optimized for 512MB-1GB memory:
- Models load lazily on first request
- Health check doesn't load models
- Memory-efficient embeddings configuration
- Single worker process

### Troubleshooting

**Service Not Starting:**
- Check **Log stream** in Azure Portal
- Verify startup command is set to `startup.sh`
- Check application settings are correct

**Out of Memory:**
- Check logs for OOM errors
- Verify you're on F1 plan (not a smaller plan)
- Consider reducing FAQ data size

**502 Bad Gateway:**
- Service might be starting (wait 30-60 seconds)
- Check logs for errors
- Verify PORT environment variable is set

**Model Download Issues:**
- First request takes 30-60 seconds to download models
- Models are cached after first download
- Check network connectivity in logs

## Updating Your Application

After making changes:

```bash
git add .
git commit -m "Your changes"
git push origin main
```

GitHub Actions will automatically deploy to Azure!

## Cost Management

**F1 Free Tier Includes:**
- 1 App Service Plan (F1 Free)
- 1 GB storage
- 1 GB memory
- 60 minutes of compute time per day

**To avoid charges:**
- Use only the F1 Free tier
- Don't create additional resources
- Monitor usage in Azure Portal → Cost Management

## Quick Reference Commands

```bash
# Azure CLI Login
az login

# List resource groups
az group list

# List web apps
az webapp list --resource-group cn-chatbot-rg

# View app settings
az webapp config appsettings list --name cn-chatbot-app --resource-group cn-chatbot-rg

# View logs
az webapp log tail --name cn-chatbot-app --resource-group cn-chatbot-rg

# Restart app
az webapp restart --name cn-chatbot-app --resource-group cn-chatbot-rg

# Delete resources (when done testing)
az group delete --name cn-chatbot-rg --yes
```

## Support

- **Azure Documentation:** [docs.microsoft.com/azure/app-service](https://docs.microsoft.com/azure/app-service)
- **Python on Azure:** [docs.microsoft.com/azure/app-service/quickstart-python](https://docs.microsoft.com/azure/app-service/quickstart-python)
- **FastAPI:** [fastapi.tiangolo.com](https://fastapi.tiangolo.com)

