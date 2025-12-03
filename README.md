# Codeninjas Chatbot Repo

A FAQ chatbot built with FastAPI, LangChain, HuggingFace embeddings, and FAISS vector store. This service provides semantic question-answering capabilities without requiring any paid API keys.

## Features

- 🚀 FastAPI backend with async support
- 🤖 LangChain integration for semantic search
- 📊 FAISS vector store for efficient similarity search
- 🎯 HuggingFace sentence-transformers (`all-MiniLM-L6-v2`) for embeddings
- 🐳 Docker containerization
- ☁️ CI/CD pipeline for Azure App Service deployment
- 
## Project Structure

```
chatbot-faq/
├── app/
│   ├── main.py              # FastAPI application entry point
│   ├── config.py            # Environment-based configuration
│   ├── models.py            # Pydantic models for request/response
│   ├── faq_data.py          # Static FAQ data storage
│   ├── chains.py            # LangChain retrieval logic
│   ├── routes/
│   │   └── faq.py          # FAQ endpoint routes
│   └── utils/
│       └── embeddings.py   # Embeddings and FAISS utilities
├── requirements.txt         # Python dependencies
├── Dockerfile              # Docker configuration
├── .env.stage              # Stage environment configuration
├── .env.production         # Production environment configuration
├── README.md               # This file
└── .github/
    └── workflows/
        └── azure-webapp.yml # GitHub Actions CI/CD pipeline
```

## Prerequisites

- Python 3.11 or higher
- pip (Python package manager)
- Docker (optional, for containerized deployment)
- Azure account (for deployment to App Service)

## Local Setup

### 1. Clone the Repository

```bash
git clone <your-repo-url>
cd chatbot-faq
```

### 2. Create Virtual Environment

```bash
# On Windows
python -m venv venv
venv\Scripts\activate

# On Linux/Mac
python3 -m venv venv
source venv/bin/activate
```

### 3. Install Dependencies

```bash
pip install -r requirements.txt
```

### 4. Configure Environment

The application supports two environments: **stage** and **production**.

**Stage Environment (Default):**
```bash
# On Windows PowerShell
$env:APP_ENV="stage"
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000

# On Windows CMD
set APP_ENV=stage
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000

# On Linux/Mac
APP_ENV=stage uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

**Production Environment:**
```bash
# On Windows PowerShell
$env:APP_ENV="production"
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000

# On Windows CMD
set APP_ENV=production
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000

# On Linux/Mac
APP_ENV=production uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

**Note:** If `APP_ENV` is not set, it defaults to `stage`. The application will automatically load the corresponding `.env.stage` or `.env.production` file.

### 5. Verify the Setup

Visit `http://localhost:8000` in your browser or check the API docs at `http://localhost:8000/docs`

Check the health endpoint to see the active environment:
```bash
curl http://localhost:8000/health
```

## Usage

### API Endpoints

#### 1. Root Endpoint (GET /)

Returns a welcome message.

**Request:**
```bash
curl http://localhost:8000/
```

**Response:**
```json
{
  "message": "Welcome to the FAQ Chatbot API! Use POST /faq/ with a question to get answers."
}
```

#### 2. FAQ Endpoint (POST /faq/)

Returns an answer to a user's question using semantic search.

**Request:**
```bash
curl -X POST "http://localhost:8000/faq/" \
  -H "Content-Type: application/json" \
  -d '{"question": "What is your return policy?"}'
```

**Using HTTPie:**
```bash
http POST http://localhost:8000/faq/ question="How can I track my order?"
```

**Response:**
```json
{
  "answer": "You can track your order by logging into your account and visiting the 'My Orders' section. You'll receive a tracking number via email once your order ships, which you can use on the carrier's website."
}
```

**Example Questions:**
- "What is your return policy?"
- "How long does shipping take?"
- "Do you ship internationally?"
- "What payment methods do you accept?"
- "Can I cancel my order?"

### Interactive API Documentation

FastAPI provides interactive API documentation:

- Swagger UI: `http://localhost:8000/docs`
- ReDoc: `http://localhost:8000/redoc`

## Docker Deployment

### Build Docker Image

```bash
docker build -t chatbot-faq .
```

### Run Docker Container

```bash
docker run -p 8000:8000 chatbot-faq
```

The API will be available at `http://localhost:8000`

## Render Deployment (Free Tier)

### Prerequisites

1. Render account (free tier available)
2. GitHub repository with code

### Deployment Steps

#### Option 1: Using render.yaml (Recommended)

1. **Push your code to GitHub:**
   ```bash
   git add .
   git commit -m "Add Render deployment configuration"
   git push origin main
   ```

2. **Connect to Render:**
   - Go to [Render Dashboard](https://dashboard.render.com/)
   - Click "New +" → "Blueprint"
   - Connect your GitHub repository
   - Render will automatically detect the `render.yaml` file
   - Click "Apply" to deploy

3. **Configure Environment Variables (Optional):**
   - Go to your service → Environment
   - Add any additional environment variables:
     - `LOCATION_SLUG_API_URL` - Location API URL (if needed)
     - `LOCATION_DATA_API_URL` - Location data API URL (if needed)
     - `LOCATION_API_KEY` - Location API key (if needed)

#### Option 2: Manual Setup

1. **Create a New Web Service:**
   - Go to [Render Dashboard](https://dashboard.render.com/)
   - Click "New +" → "Web Service"
   - Connect your GitHub repository

2. **Configure the Service:**
   - **Name:** `cn-chatbot` (or your preferred name)
   - **Runtime:** Docker
   - **Dockerfile Path:** `./Dockerfile`
   - **Docker Context:** `.`
   - **Plan:** Free

3. **Set Environment Variables:**
   - `APP_ENV` = `production`
   - `PORT` = `8000` (Render sets this automatically, but you can override)
   - `PYTHONUNBUFFERED` = `1`
   - `DEBUG` = `False`
   - Add any other required environment variables

4. **Deploy:**
   - Click "Create Web Service"
   - Render will build and deploy your application
   - The service will be available at `https://your-service-name.onrender.com`

### Important Notes for Render

- **Free Tier Limitations:**
  - Services spin down after 15 minutes of inactivity
  - First request after spin-down may take 30-60 seconds
  - Consider upgrading to a paid plan for always-on service

- **Build Time:**
  - First build may take 5-10 minutes (downloading dependencies and models)
  - Subsequent builds are faster due to caching

- **Data Persistence:**
  - The FAISS index in `data/` directory will be rebuilt on each deploy
  - For production, consider using Render's persistent disk or external storage

- **Environment Variables:**
  - Sensitive data (API keys, etc.) should be set in Render's Environment tab
  - Never commit `.env` files with sensitive data to Git

### Health Check

Render will automatically check the `/health` endpoint. Make sure it's accessible:
```bash
curl https://your-service-name.onrender.com/health
```

## Azure App Service Deployment (Free Tier)

### Prerequisites

1. Azure account (free tier available)
2. Azure CLI installed
3. GitHub repository with code

### Manual Deployment Steps

#### 1. Create Azure App Service

```bash
# Login to Azure
az login

# Create resource group
az group create --name chatbot-faq-rg --location eastus

# Create App Service Plan (Free tier)
az appservice plan create \
  --name chatbot-faq-plan \
  --resource-group chatbot-faq-rg \
  --sku FREE \
  --is-linux

# Create Web App
az webapp create \
  --name chatbot-faq-app \
  --resource-group chatbot-faq-rg \
  --plan chatbot-faq-plan \
  --deployment-container-image-name chatbot-faq:latest
```

#### 2. Configure Web App

```bash
# Set port (App Service uses PORT environment variable)
az webapp config appsettings set \
  --name chatbot-faq-app \
  --resource-group chatbot-faq-rg \
  --settings PORT=8000
```

#### 3. Deploy Using Docker

```bash
# Get publish profile
az webapp deployment list-publishing-profiles \
  --name chatbot-faq-app \
  --resource-group chatbot-faq-rg \
  --xml
```

### Automated CI/CD Deployment

The project includes a GitHub Actions workflow for automated deployment to Azure App Service.

#### Setup GitHub Actions

1. **Create Azure App Services for Stage and Production:**
   ```bash
   # Stage environment
   az webapp create \
     --name chatbot-faq-stage \
     --resource-group chatbot-faq-rg \
     --plan chatbot-faq-plan
   
   # Production environment
   az webapp create \
     --name chatbot-faq-prod \
     --resource-group chatbot-faq-rg \
     --plan chatbot-faq-plan
   ```

2. **Get Publish Profiles:**
   - Go to Azure Portal → Your App Service → Get publish profile
   - Download the `.PublishSettings` file for each environment

3. **Add GitHub Secrets:**
   - Go to your GitHub repository → Settings → Secrets and variables → Actions
   - Click "New repository secret" and add the following:
   
   **Required Secrets:**
   - `AZURE_WEBAPP_NAME_stage` - Value: `chatbot-faq-stage`
   - `AZURE_WEBAPP_NAME_production` - Value: `chatbot-faq-prod`
   - `AZURE_WEBAPP_PUBLISH_PROFILE_stage` - Copy entire content of stage `.PublishSettings` file
   - `AZURE_WEBAPP_PUBLISH_PROFILE_production` - Copy entire content of production `.PublishSettings` file
   
   **Optional (if using Docker Hub):**
   - `DOCKER_USERNAME` - Your Docker Hub username
   - `DOCKER_PASSWORD` - Your Docker Hub password

4. **Configure App Service Settings:**
   - Go to each App Service → Configuration → Application settings
   - Add: `APP_ENV` = `stage` (for stage) or `production` (for production)

5. **Push to main branch:**
   ```bash
   git add .
   git commit -m "Initial commit"
   git push origin main
   ```

The workflow will automatically:
- Build Docker images for both stage and production environments
- Deploy to respective Azure App Services using matrix strategy
- Set APP_ENV appropriately for each environment

#### Workflow Configuration

The workflow file (`.github/workflows/azure-webapp.yml`) is configured to:
- Trigger on push to `main` branch or manual workflow dispatch
- Use matrix strategy to deploy to both stage and production simultaneously
- Build Docker image with `APP_ENV` build argument
- Deploy to Azure App Service using publish profile

**Manual Deployment:**
You can also trigger deployments manually via GitHub Actions UI:
- Go to Actions → Deploy to Azure App Service → Run workflow
- Choose to deploy to "all", "stage", or "production"

**Note:** For the free tier, you may need to:
- Use Azure Container Registry (free tier) or Docker Hub
- Configure the app to pull from the registry
- Set appropriate environment variables in Azure Portal

### Environment Variables

The application supports two environments: **stage** and **production**. Configuration is managed through environment files and environment variables.

**Configuration Files:**
- `.env.stage` - Stage environment settings
- `.env.production` - Production environment settings

**Key Settings:**
- `APP_ENV` - Environment name (stage/production), default: stage
- `APP_NAME` - Application name
- `DEBUG` - Debug mode (True/False)
- `DATABASE_URL` - Database connection string (dummy values for now)
- `VECTOR_STORE_PATH` - Path to FAISS vector store index
- `PORT` - Server port (default: 8000)

**Azure App Service Settings:**

Configure these in Azure App Service Settings for each environment:

- `APP_ENV` - Set to "stage" or "production"
- `PORT=8000` (if not using default)
- `PYTHONUNBUFFERED=1` (recommended)
- `VECTOR_STORE_PATH` - Override vector store path if needed

**Example:**
```bash
# Stage environment
APP_ENV=stage
VECTOR_STORE_PATH=data/vector_stage.faiss
DEBUG=True

# Production environment
APP_ENV=production
VECTOR_STORE_PATH=data/vector_prod.faiss
DEBUG=False
```

## How It Works

1. **Initialization:**
   - FAQ data is loaded from `app/faq_data.py`
   - HuggingFace embeddings model (`all-MiniLM-L6-v2`) is initialized
   - FAISS vector store is built from FAQ questions (cached after first build)

2. **Query Processing:**
   - User submits a question via POST `/faq/`
   - Question is embedded using the sentence-transformer model
   - Semantic search is performed against the FAISS vector store
   - Most similar FAQ question is found
   - Corresponding answer is returned

3. **Caching:**
   - FAISS index is cached in `.cache/faiss_index/` directory
   - First request may take longer due to model initialization
   - Subsequent requests are faster

## Customization

### Adding More FAQs

Edit `app/faq_data.py` and add more question-answer pairs:

```python
{
    "question": "Your question here?",
    "answer": "Your answer here."
}
```

After adding FAQs, restart the application. The FAISS index will be rebuilt automatically.

### Changing Embedding Model

Edit `app/utils/embeddings.py`:

```python
EMBEDDING_MODEL = "sentence-transformers/all-mpnet-base-v2"  # Larger, more accurate
```

### Adjusting Search Results

Edit `app/chains.py`:

```python
retriever = FAQRetriever(top_k=3)  # Return top 3 results
```

## Troubleshooting

### Model Download Issues

If you encounter issues downloading the embedding model:

```bash
# Download manually
python -c "from sentence_transformers import SentenceTransformer; SentenceTransformer('sentence-transformers/all-MiniLM-L6-v2')"
```

### FAISS Index Issues

Delete the cache directory to rebuild:

```bash
rm -rf .cache/faiss_index
```

### Port Already in Use

```bash
# Use a different port
uvicorn app.main:app --port 8001
```

### Memory Issues (Free Tier)

The `all-MiniLM-L6-v2` model is lightweight (~80MB) and suitable for free tier. If you need even smaller:

- Consider using smaller models
- Reduce FAQ dataset size
- Enable swap memory if available

## Performance

- **First Request:** ~3-5 seconds (model loading + index building)
- **Subsequent Requests:** ~200-500ms (with cached index)
- **Memory Usage:** ~200-300MB (depends on FAQ size)

## License

MIT License - feel free to use this project for your own purposes.

## Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

## Support

For issues and questions:
- Open an issue on GitHub
- Check the [FastAPI documentation](https://fastapi.tiangolo.com/)
- Check the [LangChain documentation](https://python.langchain.com/)

## Acknowledgments

- [FastAPI](https://fastapi.tiangolo.com/) - Modern web framework
- [LangChain](https://www.langchain.com/) - LLM application framework
- [HuggingFace](https://huggingface.co/) - Transformers and embeddings
- [FAISS](https://github.com/facebookresearch/faiss) - Efficient similarity search
