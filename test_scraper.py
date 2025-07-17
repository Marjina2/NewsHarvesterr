#!/usr/bin/env python3
"""
Test script to verify Python scraper functionality
"""

import sys
import os
import json
import logging

# Add server directory to Python path
sys.path.append(os.path.join(os.path.dirname(__file__), 'server'))

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def test_basic_imports():
    """Test that basic imports work"""
    try:
        import requests
        import json
        import time
        import schedule
        logger.info("✅ Basic imports successful")
        return True
    except ImportError as e:
        logger.error(f"❌ Basic imports failed: {e}")
        return False

def test_scraper_services():
    """Test that scraper services can be imported"""
    try:
        from services.scraper import NewsScraper
        from services.ai_rephraser import AIRephraser
        logger.info("✅ Scraper services imported successfully")
        return True
    except ImportError as e:
        logger.error(f"❌ Scraper services import failed: {e}")
        return False

def test_scraper_functionality():
    """Test basic scraper functionality"""
    try:
        from services.scraper import NewsScraper
        scraper = NewsScraper()
        
        # Test basic functionality
        test_source = {
            'name': 'Test Source',
            'url': 'https://example.com',
            'selector': 'article',
            'isActive': True
        }
        
        # This should not crash
        articles = scraper.scrape_source(test_source['url'], test_source['name'])
        logger.info(f"✅ Scraper functionality test passed (returned {len(articles)} articles)")
        return True
    except Exception as e:
        logger.error(f"❌ Scraper functionality test failed: {e}")
        return False

def test_ai_rephraser():
    """Test AI rephraser functionality"""
    try:
        from services.ai_rephraser import AIRephraser
        rephraser = AIRephraser()
        
        # Test basic functionality (will warn if no API key)
        result = rephraser.rephrase_headline("Test headline", "Test Source")
        logger.info("✅ AI rephraser test passed")
        return True
    except Exception as e:
        logger.error(f"❌ AI rephraser test failed: {e}")
        return False

def main():
    """Run all tests"""
    logger.info("🔍 Testing Python scraper functionality...")
    
    tests = [
        ("Basic Imports", test_basic_imports),
        ("Scraper Services Import", test_scraper_services),
        ("Scraper Functionality", test_scraper_functionality),
        ("AI Rephraser", test_ai_rephraser)
    ]
    
    passed = 0
    total = len(tests)
    
    for test_name, test_func in tests:
        logger.info(f"\n--- Testing {test_name} ---")
        if test_func():
            passed += 1
    
    logger.info(f"\n📊 Test Results: {passed}/{total} tests passed")
    
    if passed == total:
        logger.info("🎉 All tests passed! Python scraper is ready for production.")
    else:
        logger.warning("⚠️  Some tests failed. Check the logs above for details.")

if __name__ == "__main__":
    main()