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

class Storage {
  constructor() {
    this.initializeDefaultData();
  }

  private async initializeDefaultData() {
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
        ];

        await db.insert(newsSources).values(defaultSources);
      }
    } catch (error) {
      console.error("Error initializing default data:", error);
    }
  }

  async getNewsSources(): Promise<NewsSource[]> {
    try {
      return await db.select().from(newsSources).orderBy(desc(newsSources.createdAt));
    } catch (error) {
      console.error("Error fetching news sources:", error);
      return [];
    }
  }

  async createNewsSource(source: InsertNewsSource): Promise<NewsSource> {
    try {
      const [newSource] = await db.insert(newsSources).values(source).returning();
      return newSource;
    } catch (error) {
      console.error("Error creating news source:", error);
      throw error;
    }
  }

  async deleteNewsSource(id: number): Promise<void> {
    try {
      await db.delete(newsSources).where(eq(newsSources.id, id));
    } catch (error) {
      console.error("Error deleting news source:", error);
      throw error;
    }
  }

  async getNewsArticles(limit: number = 50, offset: number = 0): Promise<NewsArticle[]> {
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
    try {
      const [newArticle] = await db.insert(newsArticles).values({
        ...article,
        status: "pending",
        scrapedAt: new Date(),
      }).returning();
      return newArticle;
    } catch (error) {
      console.error("Error creating news article:", error);
      throw error;
    }
  }

  async updateNewsArticleStatus(id: number, status: string, rephrasedTitle?: string): Promise<void> {
    try {
      const updateData: any = { status };
      if (rephrasedTitle) {
        updateData.rephrasedTitle = rephrasedTitle;
        updateData.rephrasedAt = new Date();
      }

      await db.update(newsArticles)
        .set(updateData)
        .where(eq(newsArticles.id, id));
    } catch (error) {
      console.error("Error updating news article status:", error);
      throw error;
    }
  }

  async getNewsArticlesByStatus(status: string): Promise<NewsArticle[]> {
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

      const [updatedConfig] = await db
        .update(scraperConfig)
        .set({
          ...configUpdate,
          updatedAt: new Date(),
        })
        .where(eq(scraperConfig.id, config.id))
        .returning();

      return updatedConfig;
    } catch (error) {
      console.error("Error updating scraper config:", error);
      throw error;
    }
  }

  async getNewsStats() {
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

      const [totalSourceStats] = await db.select({
        totalSources: sql<number>`count(*)`,
      }).from(newsSources);

      return {
        totalArticles: articleStats?.totalArticles || 0,
        todayArticles: todayStats?.todayArticles || 0,
        activeSources: sourceStats?.activeSources || 0,
        totalSources: totalSourceStats?.totalSources || 0,
      };
    } catch (error) {
      console.error("Error fetching news stats:", error);
      return {
        totalArticles: 0,
        todayArticles: 0,
        activeSources: 0,
        totalSources: 0,
      };
    }
  }
}

export const storage = new Storage();