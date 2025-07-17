
#!/usr/bin/env python3
"""
Startup script to initialize database and run the FastAPI application
"""

import os
import sys
import asyncio
import logging
from pathlib import Path

# Add server directory to Python path
server_path = Path(__file__).parent / "server"
sys.path.insert(0, str(server_path))

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

async def initialize_app():
    """Initialize the application"""
    try:
        # Import and initialize storage
        from services.storage_integration import StorageIntegration
        
        storage = StorageIntegration()
        await asyncio.to_thread(storage.connect)
        logger.info("Database initialized successfully")
        
        # Initialize NLTK data
        try:
            import nltk
            nltk.download('punkt', quiet=True)
            nltk.download('stopwords', quiet=True)
            logger.info("NLTK data initialized")
        except Exception as e:
            logger.warning(f"NLTK initialization failed: {e}")
        
        logger.info("Application initialization completed")
        
    except Exception as e:
        logger.error(f"Application initialization failed: {e}")
        sys.exit(1)

if __name__ == "__main__":
    asyncio.run(initialize_app())
