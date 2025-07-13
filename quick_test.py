#!/usr/bin/env python3
"""Quick test script to get articles with images"""

import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), 'server'))

from services.scraper import NewsScraper
from services.storage_integration import StorageIntegration
import requests
import json

def quick_test():
    # Initialize
    scraper = NewsScraper()
    storage = StorageIntegration()
    
    # Test a few reliable sources
    test_sources = [
        {"name": "BBC News", "url": "https://www.bbc.com/news", "isActive": True},
        {"name": "TechCrunch", "url": "https://techcrunch.com", "isActive": True},
        {"name": "The Verge", "url": "https://www.theverge.com", "isActive": True},
    ]
    
    all_articles = []
    for source in test_sources:
        print(f"Scraping {source['name']}...")
        try:
            articles = scraper.scrape_source(source['url'], source['name'])
            print(f"  - Got {len(articles)} articles")
            all_articles.extend(articles)
            
            # Show first article with image
            if articles:
                first_article = articles[0]
                print(f"  - First article: {first_article['title'][:50]}...")
                if first_article.get('imageUrl'):
                    print(f"  - Has image: {first_article['imageUrl'][:50]}...")
                
        except Exception as e:
            print(f"  - Error: {str(e)}")
    
    print(f"\nTotal articles: {len(all_articles)}")
    
    # Save to storage
    if all_articles:
        print("Saving articles to storage...")
        success = storage.save_scraped_articles(all_articles)
        if success:
            print("Articles saved successfully!")
        else:
            print("Some articles failed to save")

if __name__ == "__main__":
    quick_test()