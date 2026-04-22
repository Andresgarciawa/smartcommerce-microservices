"""
Main FastAPI application.
"""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
import os

from app.infrastructure.database import init_db
from app.routers import configuration

# Initialize database
init_db()

# Create FastAPI app
app = FastAPI(
    title="Configuration Service",
    description="Microservice for system configuration management",
    version="1.0.0"
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=os.getenv("CORS_ORIGINS", "*").split(","),
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(configuration.router)

# Root endpoint
@app.get("/")
def root():
    """Service information endpoint"""
    return {
        "service": "Configuration Service",
        "version": "1.0.0",
        "status": "running",
        "docs": "/docs",
        "health": "/config/health"
    }
