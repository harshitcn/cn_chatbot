# Azure GitHub Actions Setup Guide

This guide explains how to set up GitHub Actions to deploy to Azure App Service.

## Option 1: Using Azure Service Principal (Recommended)

### Step 1: Create Azure Service Principal

Run this command in Azure CLI (or Azure Cloud Shell):

```bash
az ad sp create-for-rbac --name "github-actions-cn-chatbot" \
  --role contributor \
  --scopes /subscriptions/{subscription-id}/resourceGroups/{resource-group-name} \
  --sdk-auth
```

**Replace:**
- `{subscription-id}` - Your Azure subscription ID (find it in Azure Portal → Subscriptions)
- `{resource-group-name}` - Your resource group name (e.g., `cn-chatbot-rg`)

**Example:**
```bash
az ad sp create-for-rbac --name "github-actions-cn-chatbot" \
  --role contributor \
  --scopes /subscriptions/12345678-1234-1234-1234-123456789012/resourceGroups/cn-chatbot-rg \
  --sdk-auth
```

This will output JSON like:
```json
{
  "clientId": "xxxx-xxxx-xxxx-xxxx",
  "clientSecret": "xxxx-xxxx-xxxx-xxxx",
  "subscriptionId": "xxxx-xxxx-xxxx-xxxx",
  "tenantId": "xxxx-xxxx-xxxx-xxxx",
  "activeDirectoryEndpointUrl": "https://login.microsoftonline.com",
  "resourceManagerEndpointUrl": "https://management.azure.com/",
  "activeDirectoryGraphResourceId": "https://graph.windows.net/",
  "sqlManagementEndpointUrl": "https://management.core.windows.net:8443/",
  "galleryEndpointUrl": "https://gallery.azure.com/",
  "managementEndpointUrl": "https://management.core.windows.net/"
}
```

### Step 2: Add GitHub Secret

1. Go to your GitHub repository: https://github.com/harshitcn/cn_chatbot
2. Click **Settings** → **Secrets and variables** → **Actions**
3. Click **New repository secret**
4. **Name:** `AZURE_CREDENTIALS`
5. **Value:** Paste the entire JSON output from Step 1
6. Click **Add secret**

### Step 3: Update Workflow File

The workflow file (`.github/workflows/azure-deploy.yml`) is already configured to use `AZURE_CREDENTIALS`.

Update these values in the workflow file:
- `AZURE_WEBAPP_NAME`: Your actual App Service name
- `AZURE_RESOURCE_GROUP`: Your resource group name

## Option 2: Using Publish Profile (Alternative)

If you prefer using Publish Profile instead:

### Step 1: Get Publish Profile

1. Go to Azure Portal → Your App Service
2. Click **Get publish profile** (top menu)
3. Download the `.PublishSettings` file
4. Open it in a text editor and copy ALL the XML content

### Step 2: Add GitHub Secret

1. Go to your GitHub repository → **Settings** → **Secrets and variables** → **Actions**
2. Click **New repository secret**
3. **Name:** `AZURE_WEBAPP_PUBLISH_PROFILE`
4. **Value:** Paste the entire XML content from the `.PublishSettings` file
5. Click **Add secret**

### Step 3: Update Workflow File

Change the workflow to use publish profile:

```yaml
- name: Deploy to Azure Web App
  uses: azure/webapps-deploy@v3
  with:
    app-name: ${{ env.AZURE_WEBAPP_NAME }}
    publish-profile: ${{ secrets.AZURE_WEBAPP_PUBLISH_PROFILE }}
    package: .
```

## Verify Setup

1. Go to your GitHub repository → **Actions** tab
2. You should see "Deploy to Azure App Service" workflow
3. Click **Run workflow** → **Run workflow** to test
4. Monitor the deployment logs

## Troubleshooting

**Error: "No credentials found"**
- Ensure `AZURE_CREDENTIALS` secret is set correctly
- Verify the JSON is complete and valid
- Check that the service principal has contributor role

**Error: "Site Disabled (CODE: 403)"**
- Go to Azure Portal → Your App Service → Click **Start**
- Verify the app is running

**Error: "Resource group not found"**
- Update `AZURE_RESOURCE_GROUP` in workflow file
- Verify the resource group name in Azure Portal

## Quick Setup Script

If you have Azure CLI installed, run this script:

```bash
# Set your variables
SUBSCRIPTION_ID="your-subscription-id"
RESOURCE_GROUP="cn-chatbot-rg"
SP_NAME="github-actions-cn-chatbot"

# Login to Azure
az login

# Create service principal
az ad sp create-for-rbac --name "$SP_NAME" \
  --role contributor \
  --scopes /subscriptions/$SUBSCRIPTION_ID/resourceGroups/$RESOURCE_GROUP \
  --sdk-auth

# Copy the output and add it as AZURE_CREDENTIALS secret in GitHub
```

