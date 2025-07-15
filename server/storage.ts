import { 
  NewsSource, 
  InsertNewsSource, 
  NewsArticle, 
  InsertNewsArticle, 
  ScraperConfig, 
  UpdateScraperConfig,
  NewsStats,
  newsSources,
  newsArticles,
  scraperConfig
} from "@shared/schema";
import { db } from "./db";
import { eq, desc, sql } from "drizzle-orm";

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
      name: "CNN",
      url: "https://www.cnn.com",
      isActive: true,
      createdAt: new Date(),
    });
    this.sources.set(3, {
      id: 3,
      name: "The Guardian",
      url: "https://www.theguardian.com/international",
      isActive: true,
      createdAt: new Date(),
    });
    this.sources.set(4, {
      id: 4,
      name: "NPR News",
      url: "https://www.npr.org/sections/news",
      isActive: true,
      createdAt: new Date(),
    });
    this.sources.set(5, {
      id: 5,
      name: "Associated Press",
      url: "https://apnews.com",
      isActive: true,
      createdAt: new Date(),
    });
    this.sources.set(6, {
      id: 6,
      name: "Reuters",
      url: "https://www.reuters.com",
      isActive: true,
      createdAt: new Date(),
    });
    this.sources.set(7, {
      id: 7,
      name: "TechCrunch",
      url: "https://techcrunch.com",
      isActive: true,
      createdAt: new Date(),
    });
    this.sources.set(8, {
      id: 8,
      name: "The Verge",
      url: "https://www.theverge.com",
      isActive: true,
      createdAt: new Date(),
    });
    this.sources.set(9, {
      id: 9,
      name: "Engadget",
      url: "https://www.engadget.com",
      isActive: true,
      createdAt: new Date(),
    });
    this.sources.set(10, {
      id: 10,
      name: "Ars Technica",
      url: "https://arstechnica.com",
      isActive: true,
      createdAt: new Date(),
    });
    this.sources.set(11, {
      id: 11,
      name: "WIRED",
      url: "https://www.wired.com",
      isActive: true,
      createdAt: new Date(),
    });
    this.sources.set(12, {
      id: 12,
      name: "Hacker News",
      url: "https://news.ycombinator.com",
      isActive: true,
      createdAt: new Date(),
    });
    this.currentSourceId = 13;
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

// Database Storage Implementation
export class DatabaseStorage implements IStorage {
  async getNewsSources(): Promise<NewsSource[]> {
    const sources = await db.select().from(newsSources).orderBy(desc(newsSources.createdAt));
    return sources;
  }

  async createNewsSource(source: InsertNewsSource): Promise<NewsSource> {
    const [newSource] = await db
      .insert(newsSources)
      .values(source)
      .returning();
    return newSource;
  }

  async deleteNewsSource(id: number): Promise<void> {
    await db.delete(newsSources).where(eq(newsSources.id, id));
  }

  async updateNewsSourceStatus(id: number, isActive: boolean): Promise<void> {
    await db
      .update(newsSources)
      .set({ isActive })
      .where(eq(newsSources.id, id));
  }

  async getNewsArticles(limit = 50, offset = 0): Promise<NewsArticle[]> {
    const articles = await db
      .select()
      .from(newsArticles)
      .orderBy(desc(newsArticles.scrapedAt))
      .limit(limit)
      .offset(offset);
    return articles;
  }

  async createNewsArticle(article: InsertNewsArticle): Promise<NewsArticle> {
    const [newArticle] = await db
      .insert(newsArticles)
      .values(article)
      .returning();
    return newArticle;
  }

  async updateNewsArticleStatus(id: number, status: string, rephrasedTitle?: string): Promise<void> {
    const updateData: any = { status };
    if (rephrasedTitle) {
      updateData.rephrasedTitle = rephrasedTitle;
      updateData.rephrasedAt = new Date();
    }
    
    await db
      .update(newsArticles)
      .set(updateData)
      .where(eq(newsArticles.id, id));
  }

  async getNewsArticlesByStatus(status: string): Promise<NewsArticle[]> {
    const articles = await db
      .select()
      .from(newsArticles)
      .where(eq(newsArticles.status, status))
      .orderBy(desc(newsArticles.scrapedAt));
    return articles;
  }

  async getScraperConfig(): Promise<ScraperConfig> {
    const [config] = await db.select().from(scraperConfig).limit(1);
    if (!config) {
      // Create default config if none exists
      const [newConfig] = await db
        .insert(scraperConfig)
        .values({
          intervalMinutes: 20,
          isActive: false,
        })
        .returning();
      return newConfig;
    }
    return config;
  }

  async updateScraperConfig(configUpdate: UpdateScraperConfig): Promise<ScraperConfig> {
    const [config] = await db.select().from(scraperConfig).limit(1);
    
    if (!config) {
      // Create if doesn't exist
      const [newConfig] = await db
        .insert(scraperConfig)
        .values({
          ...configUpdate,
          updatedAt: new Date(),
        })
        .returning();
      return newConfig;
    }
    
    const [updatedConfig] = await db
      .update(scraperConfig)
      .set({
        ...configUpdate,
        updatedAt: new Date(),
      })
      .where(eq(scraperConfig.id, config.id))
      .returning();
    
    return updatedConfig;
  }

  async getNewsStats(): Promise<NewsStats> {
    const today = new Date();
    today.setHours(0, 0, 0, 0);
    
    const [stats] = await db
      .select({
        totalArticles: sql<number>`count(*)`,
        todayArticles: sql<number>`count(case when ${newsArticles.scrapedAt} >= ${today} then 1 end)`,
      })
      .from(newsArticles);
    
    const [sourceStats] = await db
      .select({
        activeSources: sql<number>`count(case when ${newsSources.isActive} = true then 1 end)`,
      })
      .from(newsSources);
    
    // Calculate average per hour (mock calculation based on total articles)
    const avgPerHour = stats.totalArticles > 0 ? Math.round((stats.totalArticles / 24) * 10) / 10 : 0;
    
    return {
      totalArticles: stats.totalArticles,
      todayArticles: stats.todayArticles,
      activeSources: sourceStats.activeSources,
      avgPerHour,
    };
  }
}

export const storage = new DatabaseStorage();
