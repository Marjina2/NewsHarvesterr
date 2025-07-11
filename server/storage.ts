import { 
  NewsSource, 
  InsertNewsSource, 
  NewsArticle, 
  InsertNewsArticle, 
  ScraperConfig, 
  UpdateScraperConfig,
  NewsStats
} from "@shared/schema";

export interface IStorage {
  // News Sources
  getNewsSources(): Promise<NewsSource[]>;
  createNewsSource(source: InsertNewsSource): Promise<NewsSource>;
  deleteNewsSource(id: number): Promise<void>;
  updateNewsSourceStatus(id: number, isActive: boolean): Promise<void>;

  // News Articles
  getNewsArticles(limit?: number, offset?: number): Promise<NewsArticle[]>;
  createNewsArticle(article: InsertNewsArticle): Promise<NewsArticle>;
  updateNewsArticleStatus(id: number, status: string, rephrasedTitle?: string): Promise<void>;
  getNewsArticlesByStatus(status: string): Promise<NewsArticle[]>;

  // Scraper Configuration
  getScraperConfig(): Promise<ScraperConfig>;
  updateScraperConfig(config: UpdateScraperConfig): Promise<ScraperConfig>;

  // Statistics
  getNewsStats(): Promise<NewsStats>;
}

export class MemStorage implements IStorage {
  private sources: Map<number, NewsSource>;
  private articles: Map<number, NewsArticle>;
  private config: ScraperConfig;
  private currentSourceId: number = 1;
  private currentArticleId: number = 1;

  constructor() {
    this.sources = new Map();
    this.articles = new Map();
    this.config = {
      id: 1,
      intervalMinutes: 20,
      isActive: false,
      lastRunAt: null,
      updatedAt: new Date(),
    };

    // Add some default sources
    this.sources.set(1, {
      id: 1,
      name: "BBC News",
      url: "https://www.bbc.com/news",
      isActive: true,
      createdAt: new Date(),
    });
    this.sources.set(2, {
      id: 2,
      name: "Reuters",
      url: "https://www.reuters.com",
      isActive: true,
      createdAt: new Date(),
    });
    this.currentSourceId = 3;
  }

  async getNewsSources(): Promise<NewsSource[]> {
    return Array.from(this.sources.values());
  }

  async createNewsSource(source: InsertNewsSource): Promise<NewsSource> {
    const id = this.currentSourceId++;
    const newSource: NewsSource = {
      ...source,
      id,
      createdAt: new Date(),
    };
    this.sources.set(id, newSource);
    return newSource;
  }

  async deleteNewsSource(id: number): Promise<void> {
    this.sources.delete(id);
  }

  async updateNewsSourceStatus(id: number, isActive: boolean): Promise<void> {
    const source = this.sources.get(id);
    if (source) {
      source.isActive = isActive;
      this.sources.set(id, source);
    }
  }

  async getNewsArticles(limit = 50, offset = 0): Promise<NewsArticle[]> {
    const articles = Array.from(this.articles.values())
      .sort((a, b) => new Date(b.scrapedAt!).getTime() - new Date(a.scrapedAt!).getTime())
      .slice(offset, offset + limit);
    return articles;
  }

  async createNewsArticle(article: InsertNewsArticle): Promise<NewsArticle> {
    const id = this.currentArticleId++;
    const newArticle: NewsArticle = {
      ...article,
      id,
      status: "pending",
      rephrasedTitle: null,
      scrapedAt: new Date(),
      rephrasedAt: null,
      fullContent: article.fullContent || null,
      excerpt: article.excerpt || null,
      publishedAt: article.publishedAt ? new Date(article.publishedAt) : null,
      imageUrl: article.imageUrl || null,
      author: article.author || null,
    };
    this.articles.set(id, newArticle);
    return newArticle;
  }

  async updateNewsArticleStatus(id: number, status: string, rephrasedTitle?: string): Promise<void> {
    const article = this.articles.get(id);
    if (article) {
      article.status = status;
      if (rephrasedTitle) {
        article.rephrasedTitle = rephrasedTitle;
        article.rephrasedAt = new Date();
      }
      this.articles.set(id, article);
    }
  }

  async getNewsArticlesByStatus(status: string): Promise<NewsArticle[]> {
    return Array.from(this.articles.values()).filter(article => article.status === status);
  }

  async getScraperConfig(): Promise<ScraperConfig> {
    return this.config;
  }

  async updateScraperConfig(configUpdate: UpdateScraperConfig): Promise<ScraperConfig> {
    this.config = {
      ...this.config,
      ...configUpdate,
      updatedAt: new Date(),
    };
    return this.config;
  }

  async getNewsStats(): Promise<NewsStats> {
    const articles = Array.from(this.articles.values());
    const today = new Date();
    today.setHours(0, 0, 0, 0);
    
    const todayArticles = articles.filter(article => 
      new Date(article.scrapedAt!).getTime() >= today.getTime()
    ).length;

    const activeSources = Array.from(this.sources.values()).filter(source => source.isActive).length;

    // Calculate average per hour (mock calculation)
    const avgPerHour = articles.length > 0 ? Math.round((articles.length / 24) * 10) / 10 : 0;

    return {
      totalArticles: articles.length,
      todayArticles,
      activeSources,
      avgPerHour,
    };
  }
}

export const storage = new MemStorage();
