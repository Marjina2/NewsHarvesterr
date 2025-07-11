import requests
from bs4 import BeautifulSoup
import json
import time
from typing import List, Dict, Optional
from urllib.parse import urljoin, urlparse
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class NewsScraper:
    def __init__(self):
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
        })
        
    def scrape_bbc_news(self, url: str) -> List[Dict]:
        """Scrape BBC News headlines"""
        try:
            response = self.session.get(url, timeout=10)
            response.raise_for_status()
            
            soup = BeautifulSoup(response.content, 'html.parser')
            articles = []
            
            # BBC News specific selectors
            headlines = soup.find_all(['h2', 'h3'], class_=['sc-4fedabc7-3', 'sc-8ea7699c-3'])
            
            for headline in headlines[:10]:  # Limit to 10 articles
                title = headline.get_text(strip=True)
                if title and len(title) > 20:  # Filter out short titles
                    link_element = headline.find('a') or headline.find_parent('a')
                    article_url = ""
                    if link_element:
                        article_url = urljoin(url, link_element.get('href', ''))
                    
                    articles.append({
                        'title': title,
                        'url': article_url,
                        'source': 'BBC News'
                    })
            
            return articles
            
        except Exception as e:
            logger.error(f"Error scraping BBC News: {str(e)}")
            return []
    
    def scrape_reuters(self, url: str) -> List[Dict]:
        """Scrape Reuters headlines"""
        try:
            response = self.session.get(url, timeout=10)
            response.raise_for_status()
            
            soup = BeautifulSoup(response.content, 'html.parser')
            articles = []
            
            # Reuters specific selectors
            headlines = soup.find_all(['h2', 'h3'], class_=['story-title', 'heading'])
            
            for headline in headlines[:10]:
                title = headline.get_text(strip=True)
                if title and len(title) > 20:
                    link_element = headline.find('a') or headline.find_parent('a')
                    article_url = ""
                    if link_element:
                        article_url = urljoin(url, link_element.get('href', ''))
                    
                    articles.append({
                        'title': title,
                        'url': article_url,
                        'source': 'Reuters'
                    })
            
            return articles
            
        except Exception as e:
            logger.error(f"Error scraping Reuters: {str(e)}")
            return []
    
    def scrape_generic_news(self, url: str, source_name: str) -> List[Dict]:
        """Generic news scraper for other sources"""
        try:
            response = self.session.get(url, timeout=10)
            response.raise_for_status()
            
            soup = BeautifulSoup(response.content, 'html.parser')
            articles = []
            
            # Generic selectors for headlines
            headline_selectors = [
                'h1', 'h2', 'h3',
                '[class*="headline"]',
                '[class*="title"]',
                '[class*="story"]',
                'article h1', 'article h2', 'article h3'
            ]
            
            for selector in headline_selectors:
                headlines = soup.select(selector)
                for headline in headlines[:10]:
                    title = headline.get_text(strip=True)
                    if title and len(title) > 20:
                        link_element = headline.find('a') or headline.find_parent('a')
                        article_url = ""
                        if link_element:
                            article_url = urljoin(url, link_element.get('href', ''))
                        
                        articles.append({
                            'title': title,
                            'url': article_url,
                            'source': source_name
                        })
                        
                        if len(articles) >= 10:
                            break
                
                if len(articles) >= 10:
                    break
            
            return articles
            
        except Exception as e:
            logger.error(f"Error scraping {source_name}: {str(e)}")
            return []
    
    def scrape_source(self, url: str, source_name: str) -> List[Dict]:
        """Scrape a news source based on domain"""
        domain = urlparse(url).netloc.lower()
        
        if 'bbc.com' in domain:
            return self.scrape_bbc_news(url)
        elif 'reuters.com' in domain:
            return self.scrape_reuters(url)
        else:
            return self.scrape_generic_news(url, source_name)
    
    def scrape_all_sources(self, sources: List[Dict]) -> List[Dict]:
        """Scrape all configured news sources"""
        all_articles = []
        
        for source in sources:
            if source.get('isActive', True):
                logger.info(f"Scraping {source['name']}")
                articles = self.scrape_source(source['url'], source['name'])
                all_articles.extend(articles)
                time.sleep(1)  # Be respectful to servers
        
        return all_articles

def save_articles_to_json(articles: List[Dict], filename: str = "raw_news.json"):
    """Save scraped articles to JSON file"""
    try:
        with open(filename, 'w', encoding='utf-8') as f:
            json.dump(articles, f, ensure_ascii=False, indent=2)
        logger.info(f"Saved {len(articles)} articles to {filename}")
    except Exception as e:
        logger.error(f"Error saving articles: {str(e)}")

def load_sources_from_json(filename: str = "sources.json") -> List[Dict]:
    """Load news sources from JSON file"""
    try:
        with open(filename, 'r', encoding='utf-8') as f:
            return json.load(f)
    except FileNotFoundError:
        logger.warning(f"Sources file {filename} not found, using default sources")
        return [
            {"name": "BBC News", "url": "https://www.bbc.com/news", "isActive": True},
            {"name": "Reuters", "url": "https://www.reuters.com", "isActive": True}
        ]
    except Exception as e:
        logger.error(f"Error loading sources: {str(e)}")
        return []

if __name__ == "__main__":
    scraper = NewsScraper()
    sources = load_sources_from_json()
    articles = scraper.scrape_all_sources(sources)
    save_articles_to_json(articles)
