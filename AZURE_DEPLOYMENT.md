# Azure App Service Deployment Guide

Complete step-by-step guide to deploy your chatbot to Azure App Service.

## Prerequisites

1. **Azure Account** - Sign up at [azure.microsoft.com](https://azure.microsoft.com/free/) (free tier available)
2. **GitHub Account** - Sign up at [github.com](https://github.com) (free)
3. **Git** - Install from [git-scm.com](https://git-scm.com/)
4. **Azure CLI** (optional, for command-line deployment) - Install from [docs.microsoft.com](https://docs.microsoft.com/cli/azure/install-azure-cli)

---

## Step 1: Create GitHub Repository

### Option A: Create Repository on GitHub Website

1. **Go to GitHub:**
   - Visit [github.com](https://github.com) and sign in
   - Click the **"+"** icon in the top right → **"New repository"**

2. **Repository Settings:**
   - **Repository name:** `cn-chatbot` (or your preferred name)
   - **Description:** "Codeninjas FAQ Chatbot"
   - **Visibility:** Choose **Public** (required for free Azure tier) or **Private**
   - **Initialize:** ❌ **DO NOT** check "Add a README file" (you already have one)
   - Click **"Create repository"**

3. **Copy the repository URL:**
   - You'll see a page with setup instructions
   - Copy the repository URL (e.g., `https://github.com/yourusername/cn-chatbot.git`)

### Option B: Create Repository Using GitHub CLI

```bash
# Install GitHub CLI if not installed
# Then authenticate: gh auth login

# Create repository
gh repo create cn-chatbot --public --source=. --remote=origin --push
```

---

## Step 2: Initialize Local Git Repository

If you haven't already initialized Git in your project:

```bash
# Navigate to your project directory
cd C:\Users\harsh\Projects\cn_chatbot

# Initialize Git repository (if not already done)
git init

# Check current status
git status
```

---

## Step 3: Configure Git (First Time Only)

If this is your first time using Git on this computer:

```bash
# Set your name and email
git config --global user.name "Your Name"
git config --global user.email "your.email@example.com"
```

---

## Step 4: Add Files and Commit

```bash
# Add all files to staging
git add .

# Check what will be committed
git status

# Commit the files
git commit -m "Initial commit: Codeninjas FAQ Chatbot"

# Verify commit
git log --oneline
```

---

## Step 5: Connect to GitHub and Push

```bash
# Add GitHub repository as remote (replace with your repository URL)
git remote add origin https://github.com/yourusername/cn-chatbot.git

# Verify remote
git remote -v

# Push to GitHub (first time)
git branch -M main
git push -u origin main
```

**Note:** You may be prompted to authenticate. Use:
- **Personal Access Token** (recommended) - Create at [github.com/settings/tokens](https://github.com/settings/tokens)
- Or GitHub Desktop app for easier authentication

---

## Step 6: Create Azure Resources

### Option A: Using Azure Portal (Recommended for Beginners)

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

3. **Create App Service Plan:**
   - Click **"Create a resource"** → Search **"App Service Plan"**
   - Click **"Create"**
   - **Subscription:** Your subscription
   - **Resource Group:** `cn-chatbot-rg`
   - **Name:** `cn-chatbot-plan`
   - **Operating System:** **Linux**
   - **Region:** Same as resource group
   - **Pricing tier:** Click **"Dev/Test"** tab → Select **"F1 Free"**
   - Click **"Review + create"** → **"Create"**
   - Wait for deployment to complete (1-2 minutes)

4. **Create Web App:**
   - Click **"Create a resource"** → Search **"Web App"**
   - Click **"Create"**
   - **Subscription:** Your subscription
   - **Resource Group:** `cn-chatbot-rg`
   - **Name:** `cn-chatbot-app` (must be globally unique, add numbers if needed)
   - **Publish:** **Docker Container**
   - **Operating System:** **Linux**
   - **Region:** Same as resource group
   - **Linux Plan:** Select `cn-chatbot-plan`
   - Click **"Review + create"** → **"Create"**
   - Wait for deployment (2-3 minutes)

### Option B: Using Azure CLI

```bash
# Login to Azure
az login

# Create resource group
az group create --name cn-chatbot-rg --location eastus

# Create App Service Plan (Free tier)
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
  --deployment-container-image-name cn-chatbot:latest
```

---

## Step 7: Configure Azure App Service

### Set Environment Variables

1. **In Azure Portal:**
   - Go to your Web App → **Configuration** → **Application settings**
   - Click **"+ New application setting"** and add:

   | Name | Value |
   |------|-------|
   | `APP_ENV` | `production` |
   | `PORT` | `8000` |
   | `PYTHONUNBUFFERED` | `1` |
   | `DEBUG` | `False` |

   - Add any other environment variables you need (API keys, etc.)
   - Click **"Save"** at the top

2. **Using Azure CLI:**
```bash
az webapp config appsettings set \
  --name cn-chatbot-app \
  --resource-group cn-chatbot-rg \
  --settings \
    APP_ENV=production \
    PORT=8000 \
    PYTHONUNBUFFERED=1 \
    DEBUG=False
```

### Configure Deployment Source

1. **In Azure Portal:**
   - Go to your Web App → **Deployment Center**
   - **Source:** Select **"GitHub"**
   - Click **"Authorize"** and sign in to GitHub
   - **Organization:** Your GitHub username
   - **Repository:** `cn-chatbot` (or your repo name)
   - **Branch:** `main`
   - **Build provider:** **"GitHub Actions"** (recommended) or **"App Service build service"**
   - Click **"Save"**

---

## Step 8: Set Up GitHub Actions (Automated Deployment)

### Get Azure Publish Profile

1. **In Azure Portal:**
   - Go to your Web App → **Get publish profile**
   - Click **"Download publish profile"**
   - Save the `.PublishSettings` file (you'll need this)

### Add GitHub Secrets

1. **Go to GitHub:**
   - Navigate to your repository: `https://github.com/yourusername/cn-chatbot`
   - Click **"Settings"** → **"Secrets and variables"** → **"Actions"**
   - Click **"New repository secret"**

2. **Add Secrets:**
   - **Name:** `AZURE_WEBAPP_NAME`
     - **Value:** `cn-chatbot-app` (your Azure web app name)
   
   - **Name:** `AZURE_WEBAPP_PUBLISH_PROFILE`
     - **Value:** Open the downloaded `.PublishSettings` file in a text editor
     - Copy the **entire content** (it's XML)
     - Paste it as the value

   - Click **"Add secret"** for each

### Create GitHub Actions Workflow

The workflow file should already be created at `.github/workflows/azure-webapp.yml`. If not, it will be created automatically when you push the code.

**Verify the workflow file exists:**
```bash
# Check if workflow directory exists
ls .github/workflows/
```

---

## Step 9: Deploy to Azure

### Option A: Automatic Deployment (GitHub Actions)

1. **Push your code:**
   ```bash
   git add .
   git commit -m "Add Azure deployment configuration"
   git push origin main
   ```

2. **Monitor Deployment:**
   - Go to your GitHub repository
   - Click **"Actions"** tab
   - You should see a workflow run starting
   - Click on it to see the deployment progress
   - Wait for it to complete (5-10 minutes for first deployment)

### Option B: Manual Deployment (Docker)

If you prefer manual deployment:

```bash
# Build Docker image
docker build -t cn-chatbot:latest .

# Tag for Azure Container Registry (if using ACR)
# Or push to Docker Hub first, then configure Azure to pull from there

# Configure Azure to use your Docker image
az webapp config container set \
  --name cn-chatbot-app \
  --resource-group cn-chatbot-rg \
  --docker-custom-image-name cn-chatbot:latest
```

---

## Step 10: Verify Deployment

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

---

## Troubleshooting

### Build Fails

- **Check GitHub Actions logs:** Repository → Actions → Failed workflow → View logs
- **Common issues:**
  - Missing secrets in GitHub
  - Docker build errors
  - Incorrect web app name

### App Not Starting

- **Check Application Logs:**
  ```bash
  az webapp log tail --name cn-chatbot-app --resource-group cn-chatbot-rg
  ```
- **Verify environment variables** are set correctly
- **Check PORT** is set to 8000

### 502 Bad Gateway

- App might be starting (first request takes longer)
- Check logs for errors
- Verify Dockerfile CMD is correct

### Free Tier Limitations

- **Cold start:** First request after inactivity may take 30-60 seconds
- **Resource limits:** 1 GB storage, 1 GB memory
- **Custom domains:** Not available on free tier

---

## Updating Your Application

After making changes to your code:

```bash
# Make your changes
# ...

# Commit and push
git add .
git commit -m "Your change description"
git push origin main
```

GitHub Actions will automatically deploy the new version to Azure!

---

## Cost Management

**Free Tier Includes:**
- 1 App Service Plan (F1 Free)
- 1 GB storage
- 1 GB memory
- 60 minutes of compute time per day

**To avoid charges:**
- Use only the F1 Free tier
- Don't create additional resources
- Monitor usage in Azure Portal → Cost Management

---

## Next Steps

- **Custom Domain:** Upgrade to Basic tier for custom domains
- **Always On:** Upgrade to Basic tier to prevent cold starts
- **Scaling:** Configure auto-scaling for higher traffic
- **Monitoring:** Set up Application Insights for monitoring

---

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

---

## Support

- **Azure Documentation:** [docs.microsoft.com/azure](https://docs.microsoft.com/azure)
- **GitHub Actions:** [docs.github.com/actions](https://docs.github.com/actions)
- **FastAPI:** [fastapi.tiangolo.com](https://fastapi.tiangolo.com)

