"""
Dashboard Server - FastAPI application for dashboard services.

Run with: uvicorn src.dashboard.server:app --reload --port 8001
"""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
import logging

from .api import router, websocket_router

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)

logger = logging.getLogger(__name__)

# Create FastAPI app
app = FastAPI(
    title="Dashboard API",
    description="Real-time dashboard and observability API",
    version="2.0.0",
    docs_url="/docs",
    redoc_url="/redoc",
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "http://localhost:3001"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(router)
app.include_router(websocket_router)


@app.on_event("startup")
async def startup_event():
    """Initialize services on startup."""
    logger.info("Starting Dashboard API server...")
    
    # Initialize real-time services
    from .realtime.websocket import get_websocket_manager
    from .realtime.streaming import get_stream_manager
    from .realtime.pubsub import initialize_dashboard_topics
    
    ws_manager = get_websocket_manager()
    stream_manager = get_stream_manager()
    
    await ws_manager.start()
    await stream_manager.start()
    initialize_dashboard_topics()
    
    logger.info("Dashboard API server started successfully")


@app.on_event("shutdown")
async def shutdown_event():
    """Cleanup on shutdown."""
    logger.info("Shutting down Dashboard API server...")
    
    from .realtime.websocket import get_websocket_manager
    from .realtime.streaming import get_stream_manager
    
    ws_manager = get_websocket_manager()
    stream_manager = get_stream_manager()
    
    await ws_manager.stop()
    await stream_manager.stop()
    
    logger.info("Dashboard API server stopped")


@app.get("/")
async def root():
    """Root endpoint."""
    return {
        "service": "Dashboard API",
        "version": "2.0.0",
        "docs": "/docs",
        "health": "/api/dashboard/health",
    }


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8001, reload=True)
