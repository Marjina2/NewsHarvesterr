#!/usr/bin/env python3
"""Test script to run the scraper and save articles to the database"""

import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), 'server'))

from services.scraper import NewsScraper
from services.storage_integration import StorageIntegration
import json
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def test_scraper():
    """Test the scraper with active sources"""
    # Initialize components
    scraper = NewsScraper()
    storage = StorageIntegration()
    
    print("Getting active sources from storage...")
    sources = storage.get_active_sources()
    print(f"Found {len(sources)} active sources")
    
    if not sources:
        print("No active sources found, using default sources")
        sources = [
            {"name": "BBC News", "url": "https://www.bbc.com/news", "isActive": True},
            {"name": "TechCrunch", "url": "https://techcrunch.com", "isActive": True},
            {"name": "The Verge", "url": "https://www.theverge.com", "isActive": True},
            {"name": "Engadget", "url": "https://www.engadget.com", "isActive": True},
            {"name": "Ars Technica", "url": "https://arstechnica.com", "isActive": True},
            {"name": "WIRED", "url": "https://www.wired.com", "isActive": True},
            {"name": "Hacker News", "url": "https://news.ycombinator.com", "isActive": True}
        ]
    
    # Scrape articles
    print("Scraping articles...")
    articles = scraper.scrape_all_sources(sources)
    print(f"Scraped {len(articles)} articles")
    
    # Save articles to database
    if articles:
        print("Saving articles to database...")
        success = storage.save_scraped_articles(articles)
        if success:
            print("Articles saved successfully!")
        else:
            print("Failed to save some articles")
    else:
        print("No articles to save")

if __name__ == "__main__":
    test_scraper()