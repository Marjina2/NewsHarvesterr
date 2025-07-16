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

// In-memory storage implementation for development
class MemoryStorage implements IStorage {
  private sources: NewsSource[] = [];
  private articles: NewsArticle[] = [];
  private config: ScraperConfig;
  private nextId = 1;
  private nextArticleId = 1;

  constructor() {
    this.config = {
      id: 1,
      isActive: false,
      intervalMinutes: 30,
      lastRunAt: null,
      createdAt: new Date(),
      updatedAt: new Date()
    };
    this.initializeDefaultData();
  }

  private initializeDefaultData() {
    // Add default sources
    const defaultSources: InsertNewsSource[] = [
      { name: "BBC News", url: "https://www.bbc.com/news", isActive: true },
      { name: "Reuters", url: "https://www.reuters.com", isActive: true },
      { name: "TechCrunch", url: "https://techcrunch.com", isActive: true },
      { name: "Hacker News", url: "https://news.ycombinator.com", isActive: true },
      { name: "CNN", url: "https://www.cnn.com", isActive: true },
      { name: "The Guardian", url: "https://www.theguardian.com", isActive: true },
      { name: "NPR", url: "https://www.npr.org", isActive: true },
      { name: "Associated Press", url: "https://apnews.com", isActive: true },
      { name: "India Today", url: "https://www.indiatoday.in", isActive: true },
      { name: "NDTV", url: "https://www.ndtv.com", isActive: true },
      { name: "Times of India", url: "https://timesofindia.indiatimes.com", isActive: true },
      { name: "The Hindu", url: "https://www.thehindu.com", isActive: true },
      { name: "Economic Times", url: "https://economictimes.indiatimes.com", isActive: true },
      { name: "WIRED", url: "https://www.wired.com", isActive: true },
      { name: "Engadget", url: "https://www.engadget.com", isActive: true },
      { name: "Ars Technica", url: "https://arstechnica.com", isActive: true },
      { name: "The Verge", url: "https://www.theverge.com", isActive: true },
    ];

    defaultSources.forEach(source => {
      this.sources.push({
        ...source,
        id: this.nextId++,
        createdAt: new Date(),
        updatedAt: new Date()
      });
    });
  }

  async getNewsSources(): Promise<NewsSource[]> {
    return [...this.sources].sort((a, b) => b.createdAt.getTime() - a.createdAt.getTime());
  }

  async createNewsSource(source: InsertNewsSource): Promise<NewsSource> {
    const newSource: NewsSource = {
      ...source,
      id: this.nextId++,
      createdAt: new Date(),
      updatedAt: new Date()
    };
    this.sources.push(newSource);
    return newSource;
  }

  async deleteNewsSource(id: number): Promise<void> {
    this.sources = this.sources.filter(source => source.id !== id);
  }

  async updateNewsSourceStatus(id: number, isActive: boolean): Promise<void> {
    const source = this.sources.find(s => s.id === id);
    if (source) {
      source.isActive = isActive;
      source.updatedAt = new Date();
    }
  }

  async getNewsArticles(limit: number = 50, offset: number = 0): Promise<NewsArticle[]> {
    const sorted = [...this.articles].sort((a, b) => b.createdAt.getTime() - a.createdAt.getTime());
    return sorted.slice(offset, offset + limit);
  }

  async createNewsArticle(article: InsertNewsArticle): Promise<NewsArticle> {
    const newArticle: NewsArticle = {
      ...article,
      id: this.nextArticleId++,
      createdAt: new Date(),
      updatedAt: new Date()
    };
    this.articles.push(newArticle);
    return newArticle;
  }

  async updateNewsArticleStatus(id: number, status: string, rephrasedTitle?: string): Promise<void> {
    const article = this.articles.find(a => a.id === id);
    if (article) {
      article.status = status;
      if (rephrasedTitle) {
        article.rephrasedTitle = rephrasedTitle;
      }
      article.updatedAt = new Date();
    }
  }

  async getNewsArticlesByStatus(status: string): Promise<NewsArticle[]> {
    return this.articles.filter(article => article.status === status);
  }

  async getScraperConfig(): Promise<ScraperConfig> {
    return { ...this.config };
  }

  async updateScraperConfig(configUpdate: UpdateScraperConfig): Promise<ScraperConfig> {
    this.config = {
      ...this.config,
      ...configUpdate,
      updatedAt: new Date()
    };
    return { ...this.config };
  }

  async getNewsStats(): Promise<NewsStats> {
    const today = new Date();
    today.setHours(0, 0, 0, 0);
    
    const todayArticles = this.articles.filter(article => 
      article.createdAt >= today
    ).length;

    const activeSources = this.sources.filter(source => source.isActive).length;
    
    return {
      totalArticles: this.articles.length,
      todayArticles,
      activeSources,
      avgPerHour: todayArticles / 24
    };
  }
}

class Storage implements IStorage {
  private memoryStorage: MemoryStorage;
  private useDatabase: boolean;

  constructor() {
    this.useDatabase = db !== null;
    this.memoryStorage = new MemoryStorage();
    
    if (this.useDatabase) {
      console.log("Using database storage");
      this.initializeDefaultData();
    } else {
      console.log("Using in-memory storage for development");
    }
  }

  private async initializeDefaultData() {
    if (!this.useDatabase) return;
    
    try {
      // Check if scraper config exists, if not create it
      const existingConfig = await db.select().from(scraperConfig).limit(1);
      if (existingConfig.length === 0) {
        await db.insert(scraperConfig).values({
          isActive: false,
          intervalMinutes: 30,
        });
      }

      // Check if default sources exist, if not create them
      const existingSources = await db.select().from(newsSources);
      if (existingSources.length === 0) {
        const defaultSources: InsertNewsSource[] = [
          { name: "BBC News", url: "https://www.bbc.com/news", isActive: true },
          { name: "Reuters", url: "https://www.reuters.com", isActive: true },
          { name: "TechCrunch", url: "https://techcrunch.com", isActive: true },
          { name: "Hacker News", url: "https://news.ycombinator.com", isActive: true },
          { name: "CNN", url: "https://www.cnn.com", isActive: true },
          { name: "The Guardian", url: "https://www.theguardian.com", isActive: true },
          { name: "NPR", url: "https://www.npr.org", isActive: true },
          { name: "Associated Press", url: "https://apnews.com", isActive: true },
          { name: "India Today", url: "https://www.indiatoday.in", isActive: true },
          { name: "NDTV", url: "https://www.ndtv.com", isActive: true },
          { name: "Times of India", url: "https://timesofindia.indiatimes.com", isActive: true },
          { name: "The Hindu", url: "https://www.thehindu.com", isActive: true },
          { name: "Economic Times", url: "https://economictimes.indiatimes.com", isActive: true },
          { name: "WIRED", url: "https://www.wired.com", isActive: true },
          { name: "Engadget", url: "https://www.engadget.com", isActive: true },
          { name: "Ars Technica", url: "https://arstechnica.com", isActive: true },
          { name: "The Verge", url: "https://www.theverge.com", isActive: true },
        ];

        await db.insert(newsSources).values(defaultSources);
      }
    } catch (error) {
      console.error("Error initializing default data:", error);
    }
  }

  async getNewsSources(): Promise<NewsSource[]> {
    if (!this.useDatabase) {
      return this.memoryStorage.getNewsSources();
    }
    
    try {
      return await db.select().from(newsSources).orderBy(desc(newsSources.createdAt));
    } catch (error) {
      console.error("Error fetching news sources:", error);
      return [];
    }
  }

  async createNewsSource(source: InsertNewsSource): Promise<NewsSource> {
    if (!this.useDatabase) {
      return this.memoryStorage.createNewsSource(source);
    }
    
    try {
      const [newSource] = await db.insert(newsSources).values(source).returning();
      return newSource;
    } catch (error) {
      console.error("Error creating news source:", error);
      throw error;
    }
  }

  async deleteNewsSource(id: number): Promise<void> {
    if (!this.useDatabase) {
      return this.memoryStorage.deleteNewsSource(id);
    }
    
    try {
      await db.delete(newsSources).where(eq(newsSources.id, id));
    } catch (error) {
      console.error("Error deleting news source:", error);
      throw error;
    }
  }

  async updateNewsSourceStatus(id: number, isActive: boolean): Promise<void> {
    if (!this.useDatabase) {
      return this.memoryStorage.updateNewsSourceStatus(id, isActive);
    }
    
    try {
      await db.update(newsSources)
        .set({ isActive, updatedAt: new Date() })
        .where(eq(newsSources.id, id));
    } catch (error) {
      console.error("Error updating news source status:", error);
      throw error;
    }
  }

  async getNewsArticles(limit: number = 50, offset: number = 0): Promise<NewsArticle[]> {
    if (!this.useDatabase) {
      return this.memoryStorage.getNewsArticles(limit, offset);
    }
    
    try {
      return await db.select()
        .from(newsArticles)
        .orderBy(desc(newsArticles.scrapedAt))
        .limit(limit)
        .offset(offset);
    } catch (error) {
      console.error("Error fetching news articles:", error);
      return [];
    }
  }

  async createNewsArticle(article: InsertNewsArticle): Promise<NewsArticle> {
    if (!this.useDatabase) {
      return this.memoryStorage.createNewsArticle(article);
    }
    
    try {
      const [newArticle] = await db.insert(newsArticles).values({
        ...article,
        status: "completed", // AI rephrasing disabled
        scrapedAt: new Date(),
      }).returning();
      return newArticle;
    } catch (error) {
      console.error("Error creating news article:", error);
      throw error;
    }
  }

  async updateNewsArticleStatus(id: string | number, status: string, rephrasedTitle?: string): Promise<void> {
    if (!this.useDatabase) {
      return this.memoryStorage.updateNewsArticleStatus(id, status, rephrasedTitle);
    }
    
    try {
      const updateData: any = { status };
      if (rephrasedTitle) {
        updateData.rephrasedTitle = rephrasedTitle;
        updateData.rephrasedAt = new Date();
      }

      await db.update(newsArticles)
        .set(updateData)
        .where(eq(newsArticles.id, String(id))); // Ensure UUID is string
    } catch (error) {
      console.error("Error updating news article status:", error);
      throw error;
    }
  }

  async getNewsArticlesByStatus(status: string): Promise<NewsArticle[]> {
    if (!this.useDatabase) {
      return this.memoryStorage.getNewsArticlesByStatus(status);
    }
    
    try {
      return await db.select()
        .from(newsArticles)
        .where(eq(newsArticles.status, status))
        .orderBy(desc(newsArticles.scrapedAt));
    } catch (error) {
      console.error("Error fetching articles by status:", error);
      return [];
    }
  }

  async getScraperConfig(): Promise<ScraperConfig> {
    if (!this.useDatabase) {
      return this.memoryStorage.getScraperConfig();
    }
    
    try {
      const configs = await db.select().from(scraperConfig).limit(1);
      if (configs.length === 0) {
        // Create default config if none exists
        const [newConfig] = await db.insert(scraperConfig).values({
          isActive: false,
          intervalMinutes: 30,
        }).returning();
        return newConfig;
      }
      return configs[0];
    } catch (error) {
      console.error("Error fetching scraper config:", error);
      throw error;
    }
  }

  async updateScraperConfig(configUpdate: UpdateScraperConfig): Promise<ScraperConfig> {
    if (!this.useDatabase) {
      return this.memoryStorage.updateScraperConfig(configUpdate);
    }
    
    try {
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

      // HARDCODED STRICT RULE: Always ensure correct article distribution
      const strictConfig = {
        ...configUpdate,
        // STRICT RULE: 10 Indian + 10 International articles per source
        indianArticlesPerSource: 10,
        internationalArticlesPerSource: 10,
        // STRICT RULE: Always extract full content and enable categorization
        extractFullContent: true,
        enableCategorization: true,
        updatedAt: new Date(),
      };

      const [updatedConfig] = await db
        .update(scraperConfig)
        .set(strictConfig)
        .where(eq(scraperConfig.id, config.id))
        .returning();

      return updatedConfig;
    } catch (error) {
      console.error("Error updating scraper config:", error);
      throw error;
    }
  }

  async getNewsStats(): Promise<NewsStats> {
    if (!this.useDatabase) {
      return this.memoryStorage.getNewsStats();
    }
    
    try {
      const [articleStats] = await db.select({
        totalArticles: sql<number>`count(*)`,
      }).from(newsArticles);

      const today = new Date();
      today.setHours(0, 0, 0, 0);

      const [todayStats] = await db.select({
        todayArticles: sql<number>`count(*)`,
      }).from(newsArticles).where(sql`${newsArticles.scrapedAt} >= ${today}`);

      const [sourceStats] = await db.select({
        activeSources: sql<number>`count(*)`,
      }).from(newsSources).where(eq(newsSources.isActive, true));

      return {
        totalArticles: articleStats?.totalArticles || 0,
        todayArticles: todayStats?.todayArticles || 0,
        activeSources: sourceStats?.activeSources || 0,
        avgPerHour: (todayStats?.todayArticles || 0) / 24
      };
    } catch (error) {
      console.error("Error fetching news stats:", error);
      return {
        totalArticles: 0,
        todayArticles: 0,
        activeSources: 0,
        avgPerHour: 0
      };
    }
  }
}

export const storage = new Storage();