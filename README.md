# Codeninjas Chatbot Repo

A FAQ chatbot built with FastAPI, LangChain, HuggingFace embeddings, and FAISS vector store. This service provides semantic question-answering capabilities without requiring any paid API keys.

## Features

- 🚀 FastAPI backend with async support
- 🤖 LangChain integration for semantic search
- 📊 FAISS vector store for efficient similarity search
- 🎯 HuggingFace sentence-transformers (`all-MiniLM-L6-v2`) for embeddings
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
├── render.yaml             # Render deployment configuration
├── .env.stage              # Stage environment configuration
├── .env.production         # Production environment configuration
└── README.md               # This file
```

## Prerequisites

- Python 3.11 or higher
- pip (Python package manager)

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

## Running the Application

### Production Mode

```bash
# Set environment to production
export APP_ENV=production  # Linux/Mac
# or
set APP_ENV=production    # Windows CMD
# or
$env:APP_ENV="production" # Windows PowerShell

# Run the application
uvicorn app.main:app --host 0.0.0.0 --port 8000
```

### Stage Mode (Default)

```bash
# Stage is the default, so you can just run:
uvicorn app.main:app --host 0.0.0.0 --port 8000

# Or explicitly set it:
export APP_ENV=stage  # Linux/Mac
uvicorn app.main:app --host 0.0.0.0 --port 8000
```

The API will be available at `http://localhost:8000`

## Railway.app Deployment (Recommended - Free Tier with $5 Credit)

### Prerequisites

1. Railway account (sign up at [railway.app](https://railway.app))
2. GitHub repository with code

### Quick Start

1. **Sign up and create project:**
   - Go to [railway.app](https://railway.app)
   - Click "New Project" → "Deploy from GitHub repo"
   - Select your repository: `harshitcn/cn_chatbot`
   - Click "Deploy Now"

2. **Configure environment variables:**
   - Go to your project → **Variables** tab
   - Add these variables:
     - `APP_ENV=production`
     - `PYTHONUNBUFFERED=1`
     - `TOKENIZERS_PARALLELISM=false`
     - `OMP_NUM_THREADS=1`
     - `MKL_NUM_THREADS=1`

3. **Monitor deployment:**
   - Watch build logs in Railway dashboard
   - First deployment takes 5-10 minutes
   - Your app will be available at: `https://your-app.up.railway.app`

### Why Railway?

- ✅ **Always-on** - No spin-down (unlike Render free tier)
- ✅ **No forced timeouts** - Model loading won't be interrupted
- ✅ **Free $5 credit** monthly (usually enough for small apps)
- ✅ **Easy setup** - Automatic GitHub deployments
- ✅ **Better for ML models** - No timeout issues during model loading

### Detailed Instructions

See [RAILWAY_DEPLOYMENT.md](RAILWAY_DEPLOYMENT.md) for complete step-by-step guide.

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
   - **Runtime:** Python 3
   - **Build Command:** `pip install -r requirements.txt`
   - **Start Command:** `uvicorn app.main:app --host 0.0.0.0 --port $PORT`
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

## Azure App Service Deployment (F1 Free Tier)

### Prerequisites

1. Azure account (free tier available)
2. GitHub repository with code

### Quick Start

1. **Create Azure Resources:**
   - Follow the detailed guide in [AZURE_DEPLOYMENT.md](AZURE_DEPLOYMENT.md)
   - Or use Azure Portal to create App Service Plan (F1 Free) and Web App

2. **Configure Application Settings:**
   - Set `APP_ENV=production`
   - Set `PYTHONUNBUFFERED=1`
   - Add memory optimization variables (see AZURE_DEPLOYMENT.md)

3. **Set Startup Command:**
   - In Azure Portal → Configuration → General settings
   - Set **Startup Command** to: `startup.sh`

4. **Deploy:**
   - **Option A:** Use GitHub Actions (automated) - see `.github/workflows/azure-deploy.yml`
   - **Option B:** Use Azure CLI: `az webapp up --name your-app-name --resource-group your-rg`
   - **Option C:** Use VS Code Azure extension

### Important Notes for Azure F1 Free Tier

- **Memory:** 1 GB RAM (better than Render's 512MB)
- **No Always On:** Service may spin down after 20 minutes of inactivity
- **Cold Start:** First request after spin-down may take 30-60 seconds
- **Startup Script:** Uses `startup.sh` for optimized memory usage

### Detailed Instructions

See [AZURE_DEPLOYMENT.md](AZURE_DEPLOYMENT.md) for complete step-by-step guide including:
- Creating Azure resources
- Configuring environment variables
- Setting up GitHub Actions
- Troubleshooting tips

## Environment Variables

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
