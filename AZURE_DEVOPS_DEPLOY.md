# Azure DevOps to Azure App Service Deployment Guide

Complete guide to deploy your chatbot from Azure DevOps repository to Azure App Service F1 (Free) plan.

## Prerequisites

1. **Azure Account** - Sign up at [azure.microsoft.com/free](https://azure.microsoft.com/free/)
2. **Azure DevOps Account** - Your code is in: `https://grahamsio.visualstudio.com/Agentic%20AI/_git/Agentic%20AI`
3. **Azure App Service** - F1 Free tier Web App (create if needed)

## Quick Start: Deploy via Azure Portal

### Step 1: Create Azure App Service (if not already created)

1. Go to [portal.azure.com](https://portal.azure.com)
2. Click **"Create a resource"** → Search **"Web App"**
3. Fill in:
   - **Name:** `cn-chatbot-app` (must be globally unique)
   - **Runtime stack:** Python 3.11
   - **Operating System:** Linux
   - **App Service Plan:** Create new → F1 Free tier
   - Click **"Create"**

### Step 2: Connect Azure DevOps Repository

1. Go to your Web App in Azure Portal
2. Click **"Deployment Center"** in the left menu
3. Under **Source**, select **"Azure Repos (Git)"**
4. Click **"Authorize"** and sign in
5. Select:
   - **Organization:** `grahamsio`
   - **Project:** `Agentic AI`
   - **Repository:** `Agentic AI`
   - **Branch:** `main`
6. Click **"Save"**
7. Azure will automatically deploy your code!

### Step 3: Configure Application Settings

1. Go to **Configuration** → **Application settings**
2. Add these settings:

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

3. Click **"Save"**

### Step 4: Set Startup Command

1. Go to **Configuration** → **General settings**
2. Find **"Startup Command"**
3. Enter: `startup.sh`
4. Click **"Save"**

### Step 5: Verify Deployment

1. Go to **Overview** → Copy your app URL
2. Visit: `https://your-app-name.azurewebsites.net/health`
3. Should return: `{"status": "healthy", ...}`

## Option 2: Deploy via Azure Pipelines (CI/CD)

### Step 1: Create Azure Service Connection

1. Go to Azure DevOps: `https://dev.azure.com/grahamsio`
2. Navigate to your project: **Agentic AI**
3. Go to **Project Settings** → **Service connections**
4. Click **"New service connection"**
5. Select **"Azure Resource Manager"**
6. Select **"Workload Identity federation"** (recommended) or **"Service principal"**
7. Follow the prompts to authenticate and select your subscription
8. Name it: `Azure Service Connection`
9. Select your Azure subscription and resource group
10. Click **"Save"**

### Step 2: Create Environment (for Deployment Approval)

1. Go to **Pipelines** → **Environments**
2. Click **"Create environment"**
3. Name: `production`
4. Type: **None** (or add approval gates if needed)
5. Click **"Create"**

### Step 3: Update Pipeline Configuration

1. Go to **Pipelines** → **Pipelines**
2. Click **"New pipeline"** or edit existing
3. Select **"Azure Repos Git"**
4. Select repository: **Agentic AI**
5. Select **"Existing Azure Pipelines YAML file"**
6. Branch: `main`
7. Path: `/azure-pipelines.yml`
8. Click **"Continue"**

### Step 4: Update Variables in Pipeline

Before running, update these in `azure-pipelines.yml`:

1. **Azure Web App Name:**
   ```yaml
   azureWebAppName: 'cn-chatbot-app'  # Your actual Azure App Service name
   ```

2. **Service Connection Name:**
   ```yaml
   azureSubscription: 'Azure Service Connection'  # Match your service connection name
   ```

3. **Save and Run:**
   - The pipeline will build and deploy automatically
   - Monitor progress in the **Pipelines** tab

### Step 5: Configure Azure App Service Settings

Same as Step 3-4 in the Quick Start section above.

## Option 3: Manual Deployment via Azure CLI

### Install Azure CLI

**Windows:**
```powershell
winget install -e --id Microsoft.AzureCLI
```

### Deploy

```bash
# Login to Azure
az login

# Create resources (if not already created)
az group create --name cn-chatbot-rg --location eastus
az appservice plan create --name cn-chatbot-plan --resource-group cn-chatbot-rg --sku FREE --is-linux
az webapp create --name cn-chatbot-app --resource-group cn-chatbot-rg --plan cn-chatbot-plan --runtime "PYTHON:3.11"

# Configure startup command
az webapp config set --name cn-chatbot-app --resource-group cn-chatbot-rg --startup-file "startup.sh"

# Set application settings
az webapp config appsettings set --name cn-chatbot-app --resource-group cn-chatbot-rg \
  --settings APP_ENV=production PYTHONUNBUFFERED=1 DEBUG=False TOKENIZERS_PARALLELISM=false \
  OMP_NUM_THREADS=1 MKL_NUM_THREADS=1

# Deploy from local directory (after cloning from Azure DevOps)
az webapp up --name cn-chatbot-app --resource-group cn-chatbot-rg --runtime "PYTHON:3.11" --startup-file "startup.sh"
```

## Repository Structure

Your Azure DevOps repository should have:

```
Agentic AI/
├── app/
│   ├── main.py
│   ├── config.py
│   ├── faq_data.py
│   └── ...
├── azure-pipelines.yml  ← Pipeline configuration
├── startup.sh           ← Azure startup script
├── runtime.txt          ← Python version
├── requirements.txt     ← Python dependencies
└── README.md
```

## Continuous Deployment

### Automatic Deployment on Push

Once configured via **Deployment Center**:
- Every push to `main` branch automatically triggers deployment
- Monitor in: Azure Portal → Your Web App → **Deployment Center** → **Logs**

### Pipeline-Based Deployment

If using Azure Pipelines:
- Pipeline triggers on push to `main` branch
- Monitor in: Azure DevOps → **Pipelines** → View runs

## Important Notes

### Azure F1 Free Tier

- **Memory:** 1 GB RAM
- **Storage:** 1 GB
- **Always On:** ❌ Not available (spins down after 20 min inactivity)
- **Cold Start:** First request after spin-down takes 30-60 seconds
- **Custom Domain:** ❌ Not available on free tier

### Memory Optimization

Your app is already optimized:
- Models load lazily on first request
- Health check doesn't load models
- Single worker process
- Memory-efficient configuration

## Troubleshooting

### Deployment Fails

**Check:**
- Azure Portal → Web App → **Deployment Center** → **Logs**
- Verify startup command is set to `startup.sh`
- Check application settings are correct

### Service Not Starting

**Check:**
- Azure Portal → Web App → **Log stream**
- Verify Python version matches `runtime.txt`
- Check for errors in application logs

### Out of Memory

**Solutions:**
- Verify you're on F1 plan (1GB memory)
- Check logs for OOM errors
- Consider reducing FAQ data size
- Ensure memory optimization settings are applied

### 502 Bad Gateway

**Solutions:**
- Wait 30-60 seconds (first request loads models)
- Check Log stream for errors
- Verify PORT environment variable is set
- Check startup command is correct

## Updating Your Application

### Via Azure DevOps

1. **Make changes locally:**
   ```bash
   # Make your code changes
   git add .
   git commit -m "Your changes"
   git push azure main
   ```

2. **Automatic Deployment:**
   - If Deployment Center is connected, deployment is automatic
   - Or pipeline will trigger automatically

### Verify Deployment

1. Check deployment status:
   - Azure Portal → Web App → **Deployment Center**
   - Or Azure DevOps → **Pipelines**

2. Test your app:
   ```bash
   curl https://your-app-name.azurewebsites.net/health
   ```

## Quick Reference

### Your Repository URL
`https://grahamsio.visualstudio.com/Agentic%20AI/_git/Agentic%20AI`

### Clone Repository
```bash
git clone https://grahamsio.visualstudio.com/Agentic%20AI/_git/Agentic%20AI
```

### Push Changes
```bash
git add .
git commit -m "Your changes"
git push azure main
```

### View Pipeline Runs
Azure DevOps → Project → **Pipelines** → Select your pipeline

### View Deployment Logs
Azure Portal → Your Web App → **Deployment Center** → **Logs**

## Support

- **Azure DevOps:** [dev.azure.com](https://dev.azure.com)
- **Azure App Service Docs:** [docs.microsoft.com/azure/app-service](https://docs.microsoft.com/azure/app-service)
- **Azure Pipelines Docs:** [docs.microsoft.com/azure/devops/pipelines](https://docs.microsoft.com/azure/devops/pipelines)

