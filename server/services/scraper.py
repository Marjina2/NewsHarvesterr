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
        """Extract full article content using newspaper3k with optimized performance"""
        try:
            if not url or url.startswith('#') or url.startswith('javascript:') or not url.startswith(('http://', 'https://')):
                return {
                    'fullContent': None,
                    'excerpt': None,
                    'publishedAt': None,
                    'imageUrl': None,
                    'author': None
                }

            # Faster article extraction with shorter timeouts
            article = Article(url)
            article.config.request_timeout = 8  # Reduced timeout
            article.config.browser_user_agent = 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
            
            article.download()
            article.parse()

            # Clean and format the content
            content = article.text.strip()
            excerpt = content[:300] + "..." if len(content) > 300 else content  # Shorter excerpt

            # Extract publish date
            publish_date = None
            if article.publish_date:
                publish_date = article.publish_date.isoformat()

            # Get top image with faster validation
            image_url = None
            if article.top_image and article.top_image.startswith(('http://', 'https://')):
                # Skip validation for speed - just use the URL
                image_url = article.top_image
            
            # Quick fallback to meta tags for image
            if not image_url and hasattr(article, 'html') and article.html:
                try:
                    soup = BeautifulSoup(article.html, 'html.parser')
                    meta_image = soup.find('meta', property='og:image')
                    if meta_image and meta_image.get('content'):
                        candidate_url = meta_image.get('content')
                        if candidate_url.startswith(('http://', 'https://')):
                            image_url = candidate_url
                except:
                    pass

            return {
                'fullContent': content if content and len(content) > 50 else None,
                'excerpt': excerpt if excerpt and len(excerpt) > 20 else None,
                'publishedAt': publish_date,
                'imageUrl': image_url,
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

                        # Extract full article content
                        article_details = self.extract_full_article(article_url) if article_url else {}

                        articles.append({
                            'title': title,
                            'url': article_url,
                            'source': 'Reuters',
                            **article_details
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

                        # Extract full article content
                        article_details = self.extract_full_article(article_url) if article_url else {}

                        articles.append({
                            'title': title,
                            'url': article_url,
                            'source': source_name,
                            **article_details
                        })

                        if len(articles) >= 10:
                            break

                if len(articles) >= 10:
                    break

            return articles

        except Exception as e:
            logger.error(f"Error scraping {source_name}: {str(e)}")
            return []

    def scrape_cnn(self, url: str) -> List[Dict]:
        """Scrape CNN headlines"""
        try:
            # Try RSS feed first
            rss_url = "http://rss.cnn.com/rss/edition.rss"
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
                            'source': 'CNN',
                            **article_details
                        })

            return articles

        except Exception as e:
            logger.error(f"Error scraping CNN RSS: {str(e)}")
            # Fallback to generic scraping
            return self.scrape_generic_news(url, "CNN")

    def scrape_guardian(self, url: str) -> List[Dict]:
        """Scrape The Guardian headlines"""
        try:
            # Try RSS feed first
            rss_url = "https://www.theguardian.com/world/rss"
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
                            'source': 'The Guardian',
                            **article_details
                        })

            return articles

        except Exception as e:
            logger.error(f"Error scraping The Guardian RSS: {str(e)}")
            # Fallback to generic scraping
            return self.scrape_generic_news(url, "The Guardian")

    def scrape_npr(self, url: str) -> List[Dict]:
        """Scrape NPR headlines"""
        try:
            # Try RSS feed first
            rss_url = "https://feeds.npr.org/1001/rss.xml"
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
                            'source': 'NPR News',
                            **article_details
                        })

            return articles

        except Exception as e:
            logger.error(f"Error scraping NPR RSS: {str(e)}")
            # Fallback to generic scraping
            return self.scrape_generic_news(url, "NPR News")

    def scrape_ap(self, url: str) -> List[Dict]:
        """Scrape Associated Press headlines"""
        try:
            # Try RSS feed first
            rss_url = "https://feeds.ap.org/ApTopHeadlines"
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
                            'source': 'Associated Press',
                            **article_details
                        })

            return articles

        except Exception as e:
            logger.error(f"Error scraping Associated Press RSS: {str(e)}")
            # Fallback to generic scraping
            return self.scrape_generic_news(url, "Associated Press")

    def scrape_india_today(self, url: str) -> List[Dict]:
        """Scrape India Today headlines"""
        try:
            # Try RSS feed first as it's more reliable
            rss_url = "https://www.indiatoday.in/rss/1206578"
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
                            'source': 'India Today',
                            **article_details
                        })

            return articles

        except Exception as e:
            logger.error(f"Error scraping India Today RSS: {str(e)}")
            # Fallback to website scraping
            try:
                response = self.session.get(url, timeout=10)
                response.raise_for_status()

                soup = BeautifulSoup(response.content, 'html.parser')
                articles = []

                # India Today specific selectors
                headline_selectors = [
                    '.story-list .story-card h2 a',
                    '.lead-story h2 a',
                    '.top-news h2 a',
                    '.story h2 a',
                    '.story-list h3 a',
                    '.catagory-listing h2 a'
                ]

                for selector in headline_selectors:
                    headlines = soup.select(selector)
                    for headline in headlines[:10]:
                        title = headline.get_text(strip=True)
                        if title and len(title) > 20:
                            article_url = urljoin(url, headline.get('href', ''))

                            # Extract full article content
                            article_details = self.extract_full_article(article_url) if article_url else {}

                            articles.append({
                                'title': title,
                                'url': article_url,
                                'source': 'India Today',
                                **article_details
                            })

                            if len(articles) >= 10:
                                break

                    if len(articles) >= 10:
                        break

                return articles

            except Exception as e2:
                logger.error(f"Error scraping India Today website: {str(e2)}")
                # Final fallback to generic scraping
                return self.scrape_generic_news(url, "India Today")

    def scrape_techcrunch(self, url: str) -> List[Dict]:
        """Scrape TechCrunch headlines"""
        try:
            rss_url = "https://techcrunch.com/feed/"
            response = self.session.get(rss_url, timeout=10)
            response.raise_for_status()

            soup = BeautifulSoup(response.content, 'xml')
            articles = []

            items = soup.find_all('item')[:10]

            for item in items:
                title_elem = item.find('title')
                link_elem = item.find('link')

                if title_elem and title_elem.text:
                    title = title_elem.text.strip()
                    if len(title) > 20:
                        article_url = link_elem.text.strip() if link_elem else ""

                        article_details = self.extract_full_article(article_url) if article_url else {}

                        articles.append({
                            'title': title,
                            'url': article_url,
                            'source': 'TechCrunch',
                            **article_details
                        })

            return articles

        except Exception as e:
            logger.error(f"Error scraping TechCrunch RSS: {str(e)}")
            return self.scrape_generic_news(url, "TechCrunch")

    def scrape_wired(self, url: str) -> List[Dict]:
        """Scrape WIRED headlines"""
        try:
            rss_url = "https://www.wired.com/feed/rss"
            response = self.session.get(rss_url, timeout=10)
            response.raise_for_status()

            soup = BeautifulSoup(response.content, 'xml')
            articles = []

            items = soup.find_all('item')[:10]

            for item in items:
                title_elem = item.find('title')
                link_elem = item.find('link')

                if title_elem and title_elem.text:
                    title = title_elem.text.strip()
                    if len(title) > 20:
                        article_url = link_elem.text.strip() if link_elem else ""

                        article_details = self.extract_full_article(article_url) if article_url else {}

                        articles.append({
                            'title': title,
                            'url': article_url,
                            'source': 'WIRED',
                            **article_details
                        })

            return articles

        except Exception as e:
            logger.error(f"Error scraping WIRED RSS: {str(e)}")
            return self.scrape_generic_news(url, "WIRED")

    def scrape_engadget(self, url: str) -> List[Dict]:
        """Scrape Engadget headlines"""
        try:
            rss_url = "https://www.engadget.com/rss.xml"
            response = self.session.get(rss_url, timeout=10)
            response.raise_for_status()

            soup = BeautifulSoup(response.content, 'xml')
            articles = []

            items = soup.find_all('item')[:10]

            for item in items:
                title_elem = item.find('title')
                link_elem = item.find('link')

                if title_elem and title_elem.text:
                    title = title_elem.text.strip()
                    if len(title) > 20:
                        article_url = link_elem.text.strip() if link_elem else ""

                        article_details = self.extract_full_article(article_url) if article_url else {}

                        articles.append({
                            'title': title,
                            'url': article_url,
                            'source': 'Engadget',
                            **article_details
                        })

            return articles

        except Exception as e:
            logger.error(f"Error scraping Engadget RSS: {str(e)}")
            return self.scrape_generic_news(url, "Engadget")

    def scrape_ars_technica(self, url: str) -> List[Dict]:
        """Scrape Ars Technica headlines"""
        try:
            rss_url = "https://feeds.arstechnica.com/arstechnica/index"
            response = self.session.get(rss_url, timeout=10)
            response.raise_for_status()

            soup = BeautifulSoup(response.content, 'xml')
            articles = []

            items = soup.find_all('item')[:10]

            for item in items:
                title_elem = item.find('title')
                link_elem = item.find('link')

                if title_elem and title_elem.text:
                    title = title_elem.text.strip()
                    if len(title) > 20:
                        article_url = link_elem.text.strip() if link_elem else ""

                        article_details = self.extract_full_article(article_url) if article_url else {}

                        articles.append({
                            'title': title,
                            'url': article_url,
                            'source': 'Ars Technica',
                            **article_details
                        })

            return articles

        except Exception as e:
            logger.error(f"Error scraping Ars Technica RSS: {str(e)}")
            return self.scrape_generic_news(url, "Ars Technica")

    def scrape_verge(self, url: str) -> List[Dict]:
        """Scrape The Verge headlines"""
        try:
            rss_url = "https://www.theverge.com/rss/index.xml"
            response = self.session.get(rss_url, timeout=10)
            response.raise_for_status()

            soup = BeautifulSoup(response.content, 'xml')
            articles = []

            items = soup.find_all('item')[:10]

            for item in items:
                title_elem = item.find('title')
                link_elem = item.find('link')

                if title_elem and title_elem.text:
                    title = title_elem.text.strip()
                    if len(title) > 20:
                        article_url = link_elem.text.strip() if link_elem else ""

                        article_details = self.extract_full_article(article_url) if article_url else {}

                        articles.append({
                            'title': title,
                            'url': article_url,
                            'source': 'The Verge',
                            **article_details
                        })

            return articles

        except Exception as e:
            logger.error(f"Error scraping The Verge RSS: {str(e)}")
            return self.scrape_generic_news(url, "The Verge")

    def scrape_source(self, url: str, source_name: str) -> List[Dict]:
        """Scrape a news source based on domain"""
        domain = urlparse(url).netloc.lower()

        if 'bbc.com' in domain:
            return self.scrape_bbc_news(url)
        elif 'reuters.com' in domain:
            return self.scrape_reuters(url)
        elif 'cnn.com' in domain:
            return self.scrape_cnn(url)
        elif 'theguardian.com' in domain:
            return self.scrape_guardian(url)
        elif 'npr.org' in domain:
            return self.scrape_npr(url)
        elif 'apnews.com' in domain:
            return self.scrape_ap(url)
        elif 'ycombinator.com' in domain:
            return self.scrape_hackernews(url)
        elif 'indiatoday.in' in domain:
            return self.scrape_india_today(url)
        elif 'techcrunch.com' in domain:
            return self.scrape_techcrunch(url)
        elif 'wired.com' in domain:
            return self.scrape_wired(url)
        elif 'engadget.com' in domain:
            return self.scrape_engadget(url)
        elif 'arstechnica.com' in domain:
            return self.scrape_ars_technica(url)
        elif 'theverge.com' in domain:
            return self.scrape_verge(url)
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