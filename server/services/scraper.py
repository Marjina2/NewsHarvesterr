import requests
from bs4 import BeautifulSoup
import json
import time
from typing import List, Dict, Optional
from urllib.parse import urljoin, urlparse
import logging
from newspaper import Article
import re

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class NewsScraper:
    def __init__(self):
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
        })

    def extract_full_article(self, url: str) -> Dict:
        """Extract full article content using newspaper3k"""
        try:
            article = Article(url)
            article.download()
            article.parse()

            # Clean and format the content
            content = article.text.strip()
            excerpt = content[:300] + "..." if len(content) > 300 else content

            # Extract publish date
            publish_date = None
            if article.publish_date:
                publish_date = article.publish_date.isoformat()

            return {
                'fullContent': content,
                'excerpt': excerpt,
                'publishedAt': publish_date,
                'imageUrl': article.top_image if article.top_image else None,
                'author': ', '.join(article.authors) if article.authors else None
            }
        except Exception as e:
            logger.warning(f"Failed to extract full article from {url}: {str(e)}")
            return {
                'fullContent': None,
                'excerpt': None,
                'publishedAt': None,
                'imageUrl': None,
                'author': None
            }

    def scrape_bbc_news(self, url: str) -> List[Dict]:
        """Scrape BBC News headlines"""
        try:
            # Try RSS feed first as it's more reliable
            rss_url = "http://feeds.bbci.co.uk/news/rss.xml"
            response = self.session.get(rss_url, timeout=10)
            response.raise_for_status()

            soup = BeautifulSoup(response.content, 'xml')
            articles = []

            # Parse RSS feed - get up to 10 items
            items = soup.find_all('item')[:10]

            for item in items:
                title_elem = item.find('title')
                link_elem = item.find('link')

                if title_elem and title_elem.text:
                    title = title_elem.text.strip()
                    if len(title) > 20:
                        article_url = link_elem.text.strip() if link_elem else ""

                        # Extract full article content
                        article_details = self.extract_full_article(article_url) if article_url else {}

                        articles.append({
                            'title': title,
                            'url': article_url,
                            'source': 'BBC News',
                            **article_details
                        })

            return articles

        except Exception as e:
            logger.error(f"Error scraping BBC News RSS: {str(e)}")
            # Fallback to generic scraping
            return self.scrape_generic_news(url, "BBC News")

    def scrape_reuters(self, url: str) -> List[Dict]:
        """Scrape Reuters headlines"""
        try:
            # Try RSS feed first as it's more reliable
            rss_url = "https://feeds.reuters.com/reuters/topNews"
            response = self.session.get(rss_url, timeout=10)
            response.raise_for_status()

            soup = BeautifulSoup(response.content, 'xml')
            articles = []

            # Parse RSS feed - get up to 10 items
            items = soup.find_all('item')[:10]

            for item in items:
                title_elem = item.find('title')
                link_elem = item.find('link')

                if title_elem and title_elem.text:
                    title = title_elem.text.strip()
                    if len(title) > 20:
                        article_url = link_elem.text.strip() if link_elem else ""

                        articles.append({
                            'title': title,
                            'url': article_url,
                            'source': 'Reuters'
                        })

            return articles

        except Exception as e:
            logger.error(f"Error scraping Reuters RSS: {str(e)}")
            # Fallback to generic scraping
            return self.scrape_generic_news(url, "Reuters")

    def scrape_hackernews(self, url: str) -> List[Dict]:
        """Scrape Hacker News headlines"""
        try:
            response = self.session.get(url, timeout=10)
            response.raise_for_status()

            soup = BeautifulSoup(response.content, 'html.parser')
            articles = []

            # Hacker News specific selectors
            story_rows = soup.find_all('tr', class_='athing')[:10]

            for story in story_rows:
                title_elem = story.find('span', class_='titleline')
                if title_elem:
                    link_elem = title_elem.find('a')
                    if link_elem:
                        title = link_elem.get_text(strip=True)
                        article_url = link_elem.get('href', '')

                        # Handle relative URLs
                        if article_url.startswith('item?id='):
                            article_url = urljoin(url, article_url)

                        if title and len(title) > 20:
                            articles.append({
                                'title': title,
                                'url': article_url,
                                'source': 'Hacker News'
                            })

            return articles

        except Exception as e:
            logger.error(f"Error scraping Hacker News: {str(e)}")
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
        elif 'ycombinator.com' in domain:
            return self.scrape_hackernews(url)
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
            {"name": "Reuters", "url": "https://www.reuters.com", "isActive": True},
            {"name": "Hacker News", "url": "https://news.ycombinator.com", "isActive": True}
        ]
    except Exception as e:
        logger.error(f"Error loading sources: {str(e)}")
        return []

if __name__ == "__main__":
    scraper = NewsScraper()
    sources = load_sources_from_json()
    articles = scraper.scrape_all_sources(sources)
    save_articles_to_json(articles)