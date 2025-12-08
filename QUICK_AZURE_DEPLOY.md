# Quick Azure Deployment Guide

## Option 1: Deploy via Azure Portal (Easiest - Recommended)

### Step 1: Create Azure Resources

1. Go to [portal.azure.com](https://portal.azure.com) and sign in
2. Click **"Create a resource"** → Search **"Web App"**
3. Click **"Create"** and fill in:
   - **Subscription:** Your subscription
   - **Resource Group:** Create new → `cn-chatbot-rg`
   - **Name:** `cn-chatbot-app` (must be unique globally)
   - **Publish:** Code
   - **Runtime stack:** Python 3.11
   - **Operating System:** Linux
   - **Region:** Choose closest (e.g., East US)
   - **App Service Plan:** Create new → Name: `cn-chatbot-plan` → **Pricing tier:** F1 Free
   - Click **"Review + create"** → **"Create"**
   - Wait 2-3 minutes for deployment

### Step 2: Configure Deployment from GitHub

1. Go to your new Web App in Azure Portal
2. Click **"Deployment Center"** in the left menu
3. Under **Source**, select **"GitHub"**
4. Click **"Authorize"** and sign in to GitHub
5. Select:
   - **Organization:** `harshitcn` (your GitHub username)
   - **Repository:** `cn_chatbot`
   - **Branch:** `main`
6. Click **"Save"**
7. Azure will automatically deploy your code!

### Step 3: Configure Application Settings

1. Go to **Configuration** → **Application settings**
2. **CRITICAL:** First, add this setting to enable dependency installation:
   - **Name:** `SCM_DO_BUILD_DURING_DEPLOYMENT`
   - **Value:** `true`
   - This ensures Azure installs packages from `requirements.txt`
3. Click **"+ New application setting"** and add:

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

4. Click **"Save"** at the top

### Step 4: Set Startup Command

1. Go to **Configuration** → **General settings**
2. Find **"Startup Command"**
3. Enter: `startup.sh`
4. Click **"Save"**

### Step 5: Verify Deployment

1. Go to **Overview** → Copy your app URL
2. Visit: `https://your-app-name.azurewebsites.net/health`
3. Should return: `{"status": "healthy", ...}`

## Option 2: Deploy via GitHub Actions (Automated)

### Prerequisites
- Azure App Service already created (follow Step 1 above)

### Steps

1. **Get Publish Profile:**
   - Go to your Web App → **Get publish profile**
   - Click **"Download publish profile"**
   - Save the `.PublishSettings` file

2. **Add GitHub Secret:**
   - Go to: https://github.com/harshitcn/cn_chatbot/settings/secrets/actions
   - Click **"New repository secret"**
   - **Name:** `AZURE_WEBAPP_PUBLISH_PROFILE`
   - **Value:** Open the `.PublishSettings` file in Notepad, copy ALL the XML content, and paste it
   - Click **"Add secret"**

3. **Update Workflow File:**
   - Edit `.github/workflows/azure-deploy.yml`
   - Change line 10 to your actual app name:
     ```yaml
     AZURE_WEBAPP_NAME: cn-chatbot-app  # Your actual Azure app name
     ```

4. **Push to GitHub:**
   ```bash
   git add .github/workflows/azure-deploy.yml
   git commit -m "Update Azure workflow with app name"
   git push origin main
   ```

5. **Monitor Deployment:**
   - Go to: https://github.com/harshitcn/cn_chatbot/actions
   - Watch the deployment workflow run

## Option 3: Install Azure CLI and Deploy

### Install Azure CLI

**Windows:**
```powershell
# Download and run installer from:
# https://aka.ms/installazurecliwindows
```

Or use winget:
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
az webapp config appsettings set --name cn-chatbot-app --resource-group cn-chatbot-rg --settings APP_ENV=production PYTHONUNBUFFERED=1 DEBUG=False TOKENIZERS_PARALLELISM=false OMP_NUM_THREADS=1 MKL_NUM_THREADS=1

# Deploy from local directory
az webapp up --name cn-chatbot-app --resource-group cn-chatbot-rg --runtime "PYTHON:3.11" --startup-file "startup.sh"
```

## Troubleshooting

**Service not starting:**
- Check **Log stream** in Azure Portal
- Verify startup command is set to `startup.sh` or `python -m uvicorn app.main:app --host 0.0.0.0 --port $PORT --workers 1`
- Check application settings are correct
- **"No module named uvicorn"**: Ensure `SCM_DO_BUILD_DURING_DEPLOYMENT=true` is set, then redeploy

**502 Bad Gateway:**
- Wait 30-60 seconds (first request loads models)
- Check logs for errors
- Verify PORT environment variable

**Out of Memory:**
- Verify you're on F1 plan (1GB memory)
- Check logs for OOM errors
- Consider reducing FAQ data size

## Your App URL

After deployment, your app will be available at:
`https://cn-chatbot-app.azurewebsites.net`

(Replace `cn-chatbot-app` with your actual app name)

