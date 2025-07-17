#!/usr/bin/env python3
"""
Standalone News Scraper for Node.js Backend
This script communicates with the Node.js/Express server via API calls
"""

import sys
import os
import json
import requests
import schedule
import time
import logging
from datetime import datetime
from pathlib import Path
from typing import List, Dict, Optional

# Add server directory to Python path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

try:
    from services.scraper import NewsScraper
    from services.ai_rephraser import AIRephraser
except ImportError as e:
    print(f"Warning: Could not import scraper services: {e}")
    print("Scraper services not available - basic functionality only")
    
    # Create dummy classes for basic functionality
    class NewsScraper:
        def scrape_source(self, source):
            logger.warning("NewsScraper service not available")
            return []
    
    class AIRephraser:
        def rephrase_headline(self, headline):
            logger.warning("AIRephraser service not available")
            return headline

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class NewsScraperStandalone:
    def __init__(self, base_url: str = "http://localhost:5000"):
        self.base_url = base_url
        self.master_token = os.getenv('MASTER_TOKEN')
        self.headers = {
            'Authorization': f'Bearer {self.master_token}',
            'Content-Type': 'application/json'
        }
        
        # Initialize scraper and AI rephraser if available
        try:
            self.scraper = NewsScraper()
            self.ai_rephraser = AIRephraser()
            logger.info("Scraper services initialized successfully")
        except Exception as e:
            logger.error(f"Failed to initialize scraper services: {e}")
            self.scraper = None
            self.ai_rephraser = None

    def get_sources(self) -> List[Dict]:
        """Get active news sources from the backend"""
        try:
            response = requests.get(
                f"{self.base_url}/api/sources",
                headers=self.headers,
                timeout=30
            )
            response.raise_for_status()
            return response.json()
        except Exception as e:
            logger.error(f"Failed to get sources: {e}")
            return []

    def get_scraper_config(self) -> Dict:
        """Get scraper configuration from the backend"""
        try:
            response = requests.get(
                f"{self.base_url}/api/config",
                headers=self.headers,
                timeout=30
            )
            response.raise_for_status()
            return response.json()
        except Exception as e:
            logger.error(f"Failed to get scraper config: {e}")
            return {"intervalMinutes": 30, "isActive": False}

    def save_article(self, article: Dict) -> bool:
        """Save article to the backend"""
        try:
            response = requests.post(
                f"{self.base_url}/api/articles",
                json=article,
                headers=self.headers,
                timeout=30
            )
            response.raise_for_status()
            return True
        except Exception as e:
            logger.error(f"Failed to save article: {e}")
            return False

    def scrape_single_source(self, source: Dict) -> List[Dict]:
        """Scrape articles from a single source"""
        if not self.scraper:
            logger.error("Scraper service not available")
            return []
        
        try:
            # Use the scraper service to get articles
            articles = self.scraper.scrape_source(source)
            logger.info(f"Scraped {len(articles)} articles from {source['name']}")
            return articles
        except Exception as e:
            logger.error(f"Error scraping {source['name']}: {e}")
            return []

    def rephrase_headlines(self, articles: List[Dict]) -> List[Dict]:
        """Rephrase headlines using AI"""
        if not self.ai_rephraser:
            logger.warning("AI rephraser not available, skipping headline rephrasing")
            return articles
        
        try:
            for article in articles:
                if not article.get('rephrasedTitle'):
                    rephrased = self.ai_rephraser.rephrase_headline(article['originalTitle'])
                    if rephrased:
                        article['rephrasedTitle'] = rephrased
            return articles
        except Exception as e:
            logger.error(f"Error rephrasing headlines: {e}")
            return articles

    def run_scraper(self):
        """Run the scraper for all active sources"""
        logger.info("Starting news scraper run...")
        
        # Get configuration
        config = self.get_scraper_config()
        if not config.get('isActive', False):
            logger.info("Scraper is not active, skipping run")
            return
        
        # Get active sources
        sources = self.get_sources()
        active_sources = [s for s in sources if s.get('isActive', True)]
        
        if not active_sources:
            logger.warning("No active sources found")
            return
        
        logger.info(f"Found {len(active_sources)} active sources")
        
        total_articles = 0
        for source in active_sources:
            try:
                # Scrape articles from this source
                articles = self.scrape_single_source(source)
                
                if articles:
                    # Rephrase headlines
                    articles = self.rephrase_headlines(articles)
                    
                    # Save articles to backend
                    saved_count = 0
                    for article in articles:
                        if self.save_article(article):
                            saved_count += 1
                    
                    logger.info(f"Saved {saved_count}/{len(articles)} articles from {source['name']}")
                    total_articles += saved_count
                
            except Exception as e:
                logger.error(f"Error processing source {source['name']}: {e}")
                continue
        
        logger.info(f"Scraper run completed. Total articles saved: {total_articles}")

    def start_scheduler(self):
        """Start the scheduled scraper"""
        logger.info("Starting News Scraper Scheduler")
        
        # Get initial configuration
        config = self.get_scraper_config()
        interval = config.get('intervalMinutes', 30)
        
        # Schedule the scraper
        schedule.every(interval).minutes.do(self.run_scraper)
        
        # Run immediately if active
        if config.get('isActive', False):
            logger.info("Running initial scraper...")
            self.run_scraper()
        
        # Keep running
        while True:
            schedule.run_pending()
            time.sleep(60)  # Check every minute

def main():
    """Main function"""
    if len(sys.argv) > 1:
        command = sys.argv[1]
        
        # Use environment variable for base URL in production
        base_url = os.getenv('BASE_URL', 'http://localhost:5000')
        if os.getenv('NODE_ENV') == 'production':
            base_url = 'https://pulseebackend.onrender.com'
        
        scraper = NewsScraperStandalone(base_url)
        
        if command == 'start':
            scraper.start_scheduler()
        elif command == 'run':
            scraper.run_scraper()
        elif command == 'stop':
            logger.info("Stopping scraper...")
            sys.exit(0)
        else:
            logger.error(f"Unknown command: {command}")
            sys.exit(1)
    else:
        logger.error("Usage: python scraper_standalone.py [start|run|stop]")
        sys.exit(1)

if __name__ == "__main__":
    main()