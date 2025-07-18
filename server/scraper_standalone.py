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
            articles = self.scraper.scrape_source(source['url'], source['name'])
            logger.info(f"Scraped {len(articles)} articles from {source['name']}")
            return articles
        except Exception as e:
            logger.error(f"Error scraping {source['name']}: {e}")
            return []

    def rephrase_headlines(self, articles: List[Dict]) -> List[Dict]:
        """Skip AI rephrasing as requested by user"""
        logger.info("Skipping AI rephrasing as per user request")
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
                        # Format article for backend schema
                        published_at = article.get('publishedAt')
                        
                        # Handle different timestamp formats
                        if published_at:
                            if not isinstance(published_at, str):
                                # Convert to ISO string if it's a date object
                                try:
                                    published_at = published_at.isoformat() if hasattr(published_at, 'isoformat') else str(published_at)
                                except:
                                    published_at = None
                            elif published_at == "":
                                published_at = None
                        
                        formatted_article = {
                            'sourceName': article.get('source', source['name']),
                            'originalTitle': article.get('title', ''),
                            'originalUrl': article.get('url', ''),
                            'fullContent': article.get('fullContent', article.get('content', '')),
                            'excerpt': article.get('excerpt', ''),
                            'publishedAt': published_at,
                            'imageUrl': article.get('imageUrl', ''),
                            'author': article.get('author', ''),
                            'category': article.get('category', 'general'),
                            'region': article.get('region', 'international')
                        }
                        
                        # Debug log to help identify issues
                        logger.debug(f"Formatted article: {formatted_article['originalTitle'][:50]}...")
                        
                        if self.save_article(formatted_article):
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
        
        scraper = NewsScraperStandalone()
        
        if command == "scrape":
            # Run a single scrape operation
            logger.info("Running single scrape operation...")
            scraper.run_scraper()
            
        elif command == "run":
            # Run the scheduler (original functionality)
            logger.info("Starting scheduler...")
            scraper.start_scheduler()
            
        elif command == "test":
            # Test connection
            logger.info("Testing scraper connection...")
            sources = scraper.get_sources()
            logger.info(f"Found {len(sources)} sources")
            config = scraper.get_scraper_config()
            logger.info(f"Config: {config}")
            
        else:
            logger.error(f"Unknown command: {command}")
            logger.info("Available commands: scrape, run, test")
    else:
        logger.error("No command provided")
        logger.info("Available commands: scrape, run, test")

if __name__ == "__main__":
    main()