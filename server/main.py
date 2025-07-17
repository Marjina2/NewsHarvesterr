
#!/usr/bin/env python3
"""
FastAPI server for News Scraper Dashboard
Replaces the Node.js Express server with Python FastAPI
"""

import sys
import os
import json
import logging
from datetime import datetime
from pathlib import Path

# Add server directory to Python path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from fastapi import FastAPI, HTTPException, BackgroundTasks, Query
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from pydantic import BaseModel
from typing import Optional, List
import asyncio
import threading

from services.scheduler import NewsScraperScheduler
from services.scraper import NewsScraper
from services.storage_integration import StorageIntegration
from services.ai_rephraser import AIRephraser

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Initialize FastAPI app
app = FastAPI(title="News Scraper Dashboard", version="1.0.0")

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Initialize services
storage = StorageIntegration()
scheduler_instance = None
scheduler_thread = None

# Pydantic models for request/response
class NewsSourceCreate(BaseModel):
    name: str
    url: str
    selector: str
    category: str = "general"
    is_active: bool = True

class NewsSourceUpdate(BaseModel):
    name: Optional[str] = None
    url: Optional[str] = None
    selector: Optional[str] = None
    category: Optional[str] = None
    is_active: Optional[bool] = None

class ScraperConfigUpdate(BaseModel):
    is_active: Optional[bool] = None
    interval_minutes: Optional[int] = None

# Serve static files (React app)
current_dir = Path(__file__).parent
static_path = current_dir.parent / "dist" / "public"
if static_path.exists():
    app.mount("/static", StaticFiles(directory=str(static_path)), name="static")

@app.get("/")
async def serve_index():
    """Serve the React app"""
    index_path = static_path / "index.html"
    if index_path.exists():
        return FileResponse(str(index_path))
    return {"message": "News Scraper Dashboard API"}

# API Routes
@app.get("/api/news")
async def get_news(
    page: int = Query(1, ge=1),
    limit: int = Query(20, ge=1, le=100),
    category: Optional[str] = None,
    region: Optional[str] = None,
    source: Optional[str] = None
):
    """Get paginated news articles with filters"""
    try:
        offset = (page - 1) * limit
        articles = await asyncio.to_thread(
            storage.get_news_articles, 
            limit=limit, 
            offset=offset,
            category=category,
            region=region,
            source=source
        )
        
        total_count = await asyncio.to_thread(storage.get_total_articles_count)
        
        return {
            "articles": articles,
            "pagination": {
                "page": page,
                "limit": limit,
                "total": total_count,
                "pages": (total_count + limit - 1) // limit
            }
        }
    except Exception as e:
        logger.error(f"Error fetching news: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to fetch news articles")

@app.get("/api/sources")
async def get_sources():
    """Get all news sources"""
    try:
        sources = await asyncio.to_thread(storage.get_news_sources)
        return sources
    except Exception as e:
        logger.error(f"Error fetching sources: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to fetch sources")

@app.post("/api/sources")
async def create_source(source: NewsSourceCreate):
    """Create a new news source"""
    try:
        new_source = await asyncio.to_thread(storage.create_news_source, source.dict())
        return new_source
    except Exception as e:
        logger.error(f"Error creating source: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to create source")

@app.put("/api/sources/{source_id}")
async def update_source(source_id: int, source_update: NewsSourceUpdate):
    """Update a news source"""
    try:
        updated_source = await asyncio.to_thread(
            storage.update_news_source, 
            source_id, 
            source_update.dict(exclude_unset=True)
        )
        if not updated_source:
            raise HTTPException(status_code=404, detail="Source not found")
        return updated_source
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error updating source: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to update source")

@app.delete("/api/sources/{source_id}")
async def delete_source(source_id: int):
    """Delete a news source"""
    try:
        success = await asyncio.to_thread(storage.delete_news_source, source_id)
        if not success:
            raise HTTPException(status_code=404, detail="Source not found")
        return {"message": "Source deleted successfully"}
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error deleting source: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to delete source")

@app.get("/api/config")
async def get_config():
    """Get scraper configuration"""
    try:
        config = await asyncio.to_thread(storage.get_scraper_config)
        return config
    except Exception as e:
        logger.error(f"Error fetching config: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to fetch configuration")

@app.put("/api/config")
async def update_config(config_update: ScraperConfigUpdate):
    """Update scraper configuration"""
    try:
        updated_config = await asyncio.to_thread(
            storage.update_scraper_config, 
            config_update.dict(exclude_unset=True)
        )
        return updated_config
    except Exception as e:
        logger.error(f"Error updating config: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to update configuration")

@app.post("/api/scraper/start")
async def start_scraper(background_tasks: BackgroundTasks):
    """Start the news scraper"""
    global scheduler_instance, scheduler_thread
    
    try:
        # Update config to active
        await asyncio.to_thread(storage.update_scraper_config, {"is_active": True})
        
        # Start scheduler in background if not already running
        if scheduler_thread is None or not scheduler_thread.is_alive():
            scheduler_instance = NewsScraperScheduler()
            scheduler_thread = threading.Thread(target=scheduler_instance.start_scheduler, daemon=True)
            scheduler_thread.start()
            logger.info("Started scraper scheduler thread")
        
        return {"success": True, "message": "Scraper started successfully"}
    except Exception as e:
        logger.error(f"Error starting scraper: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to start scraper")

@app.post("/api/scraper/stop")
async def stop_scraper():
    """Stop the news scraper"""
    global scheduler_instance
    
    try:
        # Update config to inactive
        await asyncio.to_thread(storage.update_scraper_config, {"is_active": False})
        
        # Stop scheduler if running
        if scheduler_instance:
            scheduler_instance.stop_scheduler()
            logger.info("Stopped scraper scheduler")
        
        return {"success": True, "message": "Scraper stopped successfully"}
    except Exception as e:
        logger.error(f"Error stopping scraper: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to stop scraper")

@app.post("/api/scraper/test")
async def test_scraper():
    """Test scraper functionality"""
    try:
        scraper = NewsScraper()
        sources = await asyncio.to_thread(storage.get_active_sources)
        
        if not sources:
            return {"success": False, "message": "No active sources configured"}
        
        # Test with first source
        test_source = sources[0]
        articles = await asyncio.to_thread(scraper.scrape_single_source, test_source)
        
        return {
            "success": True,
            "message": f"Test successful - scraped {len(articles)} articles from {test_source['name']}",
            "articles_count": len(articles)
        }
    except Exception as e:
        logger.error(f"Error testing scraper: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Scraper test failed: {str(e)}")

@app.get("/api/stats")
async def get_stats():
    """Get dashboard statistics"""
    try:
        stats = await asyncio.to_thread(storage.get_news_stats)
        return stats
    except Exception as e:
        logger.error(f"Error fetching stats: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to fetch statistics")

@app.on_event("startup")
async def startup_event():
    """Initialize the application on startup"""
    logger.info("Starting News Scraper Dashboard API")
    
    # Initialize database connection
    try:
        await asyncio.to_thread(storage.connect)
        logger.info("Database connection established")
    except Exception as e:
        logger.error(f"Database connection failed: {str(e)}")

@app.on_event("shutdown")
async def shutdown_event():
    """Cleanup on shutdown"""
    global scheduler_instance
    
    logger.info("Shutting down News Scraper Dashboard API")
    
    # Stop scheduler if running
    if scheduler_instance:
        scheduler_instance.stop_scheduler()
        logger.info("Stopped scraper scheduler")

# Catch-all route for React app (must be last)
@app.get("/{full_path:path}")
async def serve_react_app(full_path: str):
    """Serve React app for all non-API routes"""
    index_path = static_path / "index.html"
    if index_path.exists():
        return FileResponse(str(index_path))
    raise HTTPException(status_code=404, detail="Not found")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=10000)
