"""
FastAPI application main entry point.
Initializes the FastAPI app with routes and middleware.
"""
import logging
from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.models import WelcomeResponse
from app.routes import faq, events, cron
from app.config import get_settings
from app.chains import get_retriever
from app.database import init_db
from app.utils.cron_service import CronService

# Get settings based on environment
settings = get_settings()

# Configure logging
logging.basicConfig(
    level=logging.DEBUG if settings.debug else logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)

# Global cron service instance
cron_service: CronService = None


@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Lifespan context manager for startup and shutdown events.
    Note: Retriever is loaded lazily on first request to save memory on free tier.
    """
    global cron_service
    
    # Startup: Initialize database and start cron service
    logger.info("🚀 Starting up application...")
    logger.info(f"Environment: {settings.app_env.upper()}")
    logger.info(f"Vector store path: {settings.vector_store_path}")
    logger.info(f"Database URL: {settings.database_url}")
    
    # Initialize database
    try:
        logger.info("Initializing database...")
        init_db()
        logger.info("Database initialized successfully")
    except Exception as e:
        logger.error(f"Error initializing database: {str(e)}", exc_info=True)
    
    # Start cron service if enabled
    if settings.cron_enabled:
        try:
            logger.info("Starting cron service...")
            cron_service = CronService()
            cron_service.start_scheduler(settings.cron_schedule)
            logger.info(f"Cron service started with schedule: {settings.cron_schedule}")
            logger.info(f"Next run: {cron_service.get_next_run_time()}")
        except Exception as e:
            logger.error(f"Error starting cron service: {str(e)}", exc_info=True)
    else:
        logger.info("Cron service is disabled")
    
    logger.info("📝 Retriever will be loaded lazily on first request to optimize memory usage")
    logger.info("✅ Application ready to serve requests")
    
    yield
    
    # Shutdown: Clean up
    logger.info("🛑 Shutting down application...")
    
    # Stop cron service
    if cron_service:
        try:
            cron_service.stop_scheduler()
            logger.info("Cron service stopped")
        except Exception as e:
            logger.error(f"Error stopping cron service: {str(e)}")
    
    # Clean up retriever if loaded
    try:
        from app.chains import _retriever
        if _retriever is not None:
            logger.info("Cleaning up retriever...")
    except:
        pass


# Initialize FastAPI application
app = FastAPI(
    title=settings.app_name,
    description="Codeninjas FAQ chatbot using LangChain with HuggingFace embeddings and FAISS",
    version="1.0.0",
    debug=settings.debug,
    lifespan=lifespan
)

# Log environment information
logger.info(f"Starting application in {settings.app_env.upper()} mode")
logger.info(f"Debug mode: {settings.debug}")
logger.info(f"Vector store path: {settings.vector_store_path}")
logger.info(f"Database URL: {settings.database_url}")

# Configure CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # In production, specify allowed origins
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(faq.router)
app.include_router(events.router)
app.include_router(cron.router)


@app.get("/", response_model=WelcomeResponse)
async def root() -> WelcomeResponse:
    """
    Root endpoint returning welcome message.
    
    Returns:
        WelcomeResponse: Welcome message
    """
    env_info = f" (Environment: {settings.app_env.upper()})" if settings.debug else ""
    return WelcomeResponse(
        message=f"Welcome to Code Ninjas! Are you interested in a Program or a Franchisee? Which role fits you the best?,['General Information', 'Parents & Students', 'Franchise Business']"
    )


@app.get("/health")
async def health_check():
    """
    Health check endpoint for monitoring.
    Does NOT load the retriever to avoid memory issues on Render free tier.
    """
    return {
        "status": "healthy",
        "environment": settings.app_env,
        "debug": settings.debug,
        "message": "Service is running. FAQ endpoint will load models on first request."
    }

