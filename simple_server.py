#!/usr/bin/env python3
"""
Simple test server for Local Writing Assistant
Starts server without complex service initialization
"""

import sys
import os

# Add current directory to Python path
sys.path.insert(0, os.getcwd())

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Create simple FastAPI app
app = FastAPI(
    title="Local Writing Assistant",
    description="Privacy-first, offline grammar and writing assistance",
    version="1.0.0"
)

# CORS configuration for Chrome extension
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "chrome-extension://*",
        "moz-extension://*", 
        "http://127.0.0.1:8000",
        "http://localhost:8000"
    ],
    allow_credentials=False,
    allow_methods=["GET", "POST", "OPTIONS"],
    allow_headers=["*"],
)

@app.get("/")
async def root():
    """Root endpoint"""
    return {
        "message": "Local Writing Assistant API",
        "version": "1.0.0", 
        "status": "running",
        "docs": "/docs"
    }

@app.get("/health")
async def health():
    """Basic health check"""
    return {
        "ok": True,
        "message": "Service is healthy",
        "version": "1.0.0"
    }

@app.get("/api/status")
async def api_status():
    """API status endpoint"""
    return {
        "api": "Local Writing Assistant",
        "version": "1.0.0",
        "status": "online",
        "available_endpoints": [
            "/health - Basic health check",
            "/docs - API documentation",
            "/api/status - This endpoint"
        ],
        "note": "This is a simplified test server. Full features may not be available."
    }

if __name__ == "__main__":
    import uvicorn
    
    print("=" * 60)
    print("LOCAL WRITING ASSISTANT - SIMPLE TEST SERVER")
    print("=" * 60)
    print("Starting server at http://127.0.0.1:8000")
    print("API docs: http://127.0.0.1:8000/docs")
    print("Health check: http://127.0.0.1:8000/health")
    print("=" * 60)
    
    uvicorn.run(
        app,
        host="127.0.0.1", 
        port=8000,
        log_level="info"
    )
