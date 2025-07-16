#!/usr/bin/env python3
"""Test script to verify the strict 20 articles per source rule enforcement"""

import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), 'server'))

from services.scraper import NewsScraper
from services.storage_integration import StorageIntegration

def test_strict_scraper():
    """Test the scraper with strict 20 articles per source rule"""
    print("Testing strict scraper rule enforcement...")
    
    # Initialize components
    scraper = NewsScraper()
    storage = StorageIntegration()
    
    # Get active sources
    sources = storage.get_active_sources()
    print(f"Found {len(sources)} active sources")
    
    # Test scraping with strict rules
    print("\n" + "="*60)
    print("TESTING STRICT RULE: 20 articles per source (10 Indian + 10 International)")
    print("="*60)
    
    # Scrape all sources
    all_articles = scraper.scrape_all_sources(sources)
    
    # Validate results
    print(f"\nFinal validation:")
    print(f"Total articles scraped: {len(all_articles)}")
    print(f"Expected articles: {len(sources) * 20}")
    
    # Check distribution per source
    source_counts = {}
    indian_counts = {}
    international_counts = {}
    
    for article in all_articles:
        source = article.get('source', 'unknown')
        region = article.get('region', 'international')
        
        source_counts[source] = source_counts.get(source, 0) + 1
        
        if region == 'indian':
            indian_counts[source] = indian_counts.get(source, 0) + 1
        else:
            international_counts[source] = international_counts.get(source, 0) + 1
    
    print(f"\nDistribution per source:")
    for source in sources:
        if source.get('isActive', True):
            source_name = source['name']
            total = source_counts.get(source_name, 0)
            indian = indian_counts.get(source_name, 0)
            international = international_counts.get(source_name, 0)
            
            print(f"  {source_name}: {total} articles (Indian: {indian}, International: {international})")
            
            # Check if rules are followed
            if total != 20:
                print(f"    ⚠️  WARNING: Expected 20 articles, got {total}")
            if indian > 10:
                print(f"    ⚠️  WARNING: Too many Indian articles ({indian})")
            if international > 10:
                print(f"    ⚠️  WARNING: Too many International articles ({international})")
    
    # Check content quality
    content_quality = {
        'with_full_content': 0,
        'with_images': 0,
        'with_authors': 0,
        'with_published_date': 0
    }
    
    for article in all_articles:
        if article.get('fullContent') and len(article.get('fullContent', '')) > 100:
            content_quality['with_full_content'] += 1
        if article.get('imageUrl'):
            content_quality['with_images'] += 1
        if article.get('author'):
            content_quality['with_authors'] += 1
        if article.get('publishedAt'):
            content_quality['with_published_date'] += 1
    
    print(f"\nContent Quality Assessment:")
    print(f"  Articles with full content: {content_quality['with_full_content']}/{len(all_articles)}")
    print(f"  Articles with images: {content_quality['with_images']}/{len(all_articles)}")
    print(f"  Articles with authors: {content_quality['with_authors']}/{len(all_articles)}")
    print(f"  Articles with published dates: {content_quality['with_published_date']}/{len(all_articles)}")
    
    # Test saving to storage
    print(f"\nTesting storage integration...")
    success = storage.save_scraped_articles(all_articles)
    if success:
        print("✅ Successfully saved articles to storage")
    else:
        print("❌ Failed to save articles to storage")
    
    print(f"\nTest completed!")
    return all_articles

if __name__ == "__main__":
    test_strict_scraper()