"""
StylistAI - Trend-Aware Personal Styling Assistant
Main FastAPI application entry point
"""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from fastapi.staticfiles import StaticFiles
import logging
import os

from app.config import settings
from app.core.security import initialize_firebase
from app.core.datadog import init_datadog, shutdown_datadog
from app.api import auth, styling, onboarding

# Configure logging
logging.basicConfig(
    level=settings.LOG_LEVEL,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Initialize FastAPI app
app = FastAPI(
    title=settings.APP_NAME,
    version=settings.APP_VERSION,
    description="Trend-aware personal styling assistant with visual memory",
    docs_url="/docs",
    redoc_url="/redoc",
)

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins_list,
    allow_credentials=settings.CORS_ALLOW_CREDENTIALS,
    allow_methods=settings.CORS_ALLOW_METHODS,
    allow_headers=settings.CORS_ALLOW_HEADERS,
)


# Startup event
@app.on_event("startup")
async def startup_event():
    """Initialize services on application startup"""
    logger.info("Starting StylistAI API...")

    # Initialize Datadog LLM Observability (first, to capture everything)
    try:
        datadog_enabled = init_datadog(settings)
        if datadog_enabled:
            logger.info("✅ Datadog LLM Observability initialized")
        else:
            logger.info("ℹ️ Datadog LLM Observability not enabled (DD_API_KEY not set)")
    except Exception as e:
        logger.error(f"Failed to initialize Datadog: {e}")
        logger.warning("API will start but monitoring will not work")

    # Initialize Firebase
    try:
        initialize_firebase()
        logger.info("Firebase initialized successfully")
    except Exception as e:
        logger.error(f"Failed to initialize Firebase: {e}")
        logger.warning("API will start but authentication will not work")

    # Initialize Database
    try:
        from app.database import init_db
        init_db()
        logger.info("Database initialized successfully")
    except Exception as e:
        logger.error(f"Failed to initialize database: {e}")
        logger.warning("API will start but database features will not work")


# Shutdown event
@app.on_event("shutdown")
async def shutdown_event():
    """Cleanup on application shutdown"""
    logger.info("Shutting down StylistAI API...")

    # Shutdown Datadog
    try:
        shutdown_datadog()
        logger.info("Datadog monitoring shut down")
    except Exception as e:
        logger.error(f"Error shutting down Datadog: {e}")


@app.get("/api")
async def root():
    """API info endpoint"""
    return {
        "app": settings.APP_NAME,
        "version": settings.APP_VERSION,
        "status": "healthy",
        "message": "Welcome to StylistAI API",
    }


@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {
        "status": "healthy",
        "service": "StylistAI API",
    }


# Exception handlers
@app.exception_handler(404)
async def not_found_handler(request, exc):
    return JSONResponse(
        status_code=404,
        content={"detail": "Resource not found"},
    )


@app.exception_handler(500)
async def internal_error_handler(request, exc):
    return JSONResponse(
        status_code=500,
        content={"detail": "Internal server error"},
    )


# Include API routers
app.include_router(auth.router, prefix="/auth", tags=["Authentication"])
app.include_router(onboarding.router, tags=["Onboarding"])
app.include_router(styling.router, tags=["Styling"])
# TODO: Add more routers as they're implemented
# app.include_router(outfits.router, prefix="/outfits", tags=["Outfits"])

# Serve uploaded images (mount BEFORE frontend to avoid conflicts)
uploads_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), "uploads")
os.makedirs(uploads_path, exist_ok=True)  # Create uploads dir if doesn't exist
app.mount("/uploads", StaticFiles(directory=uploads_path), name="uploads")
logger.info(f"Serving uploaded files from: {uploads_path}")

# Serve static frontend files
frontend_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), "frontend")
if os.path.exists(frontend_path):
    app.mount("/", StaticFiles(directory=frontend_path, html=True), name="static")
    logger.info(f"Serving static files from: {frontend_path}")
else:
    logger.warning(f"Frontend directory not found: {frontend_path}")


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(
        "app.main:app",
        host=settings.HOST,
        port=settings.PORT,
        reload=settings.DEBUG,
    )
