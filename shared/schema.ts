import { pgTable, text, serial, integer, boolean, timestamp, jsonb } from "drizzle-orm/pg-core";
import { createInsertSchema } from "drizzle-zod";
import { z } from "zod";

// News Sources
export const newsSources = pgTable("news_sources", {
  id: serial("id").primaryKey(),
  name: text("name").notNull(),
  url: text("url").notNull().unique(),
  isActive: boolean("is_active").default(true),
  createdAt: timestamp("created_at").defaultNow(),
});

// News Articles
export const newsArticles = pgTable("news_articles", {
  id: serial("id").primaryKey(),
  sourceId: integer("source_id").references(() => newsSources.id),
  sourceName: text("source_name").notNull(),
  originalTitle: text("original_title").notNull(),
  rephrasedTitle: text("rephrased_title"),
  originalUrl: text("original_url"),
  fullContent: text("full_content"),
  excerpt: text("excerpt"),
  publishedAt: timestamp("published_at"),
  imageUrl: text("image_url"),
  author: text("author"),
  category: text("category").default("general"), // general, technology, politics, sports, business, entertainment, health, science, indian
  region: text("region").default("international"), // indian, international
  status: text("status").notNull().default("pending"), // pending, processing, completed, failed
  scrapedAt: timestamp("scraped_at").defaultNow(),
  rephrasedAt: timestamp("rephrased_at"),
});

// Scraper Configuration
export const scraperConfig = pgTable("scraper_config", {
  id: serial("id").primaryKey(),
  intervalMinutes: integer("interval_minutes").notNull().default(20),
  isActive: boolean("is_active").default(false),
  lastRunAt: timestamp("last_run_at"),
  updatedAt: timestamp("updated_at").defaultNow(),
});

// Zod schemas for validation
export const insertNewsSourceSchema = createInsertSchema(newsSources).pick({
  name: true,
  url: true,
  isActive: true,
});

export const insertNewsArticleSchema = createInsertSchema(newsArticles).pick({
  sourceId: true,
  sourceName: true,
  originalTitle: true,
  originalUrl: true,
  fullContent: true,
  excerpt: true,
  publishedAt: true,
  imageUrl: true,
  author: true,
  category: true,
  region: true,
}).extend({
  originalTitle: z.string().min(1, "Title is required"),
  sourceName: z.string().min(1, "Source name is required"),
  originalUrl: z.string().optional().nullable(),
  imageUrl: z.string().optional().nullable(),
  category: z.string().optional(),
  region: z.string().optional(),
});

export const updateScraperConfigSchema = createInsertSchema(scraperConfig).pick({
  intervalMinutes: true,
  isActive: true,
});

// Types
export type NewsSource = typeof newsSources.$inferSelect;
export type InsertNewsSource = z.infer<typeof insertNewsSourceSchema>;

export type NewsArticle = typeof newsArticles.$inferSelect;
export type InsertNewsArticle = z.infer<typeof insertNewsArticleSchema>;

export type ScraperConfig = typeof scraperConfig.$inferSelect;
export type UpdateScraperConfig = z.infer<typeof updateScraperConfigSchema>;

// API Response types
export type ScraperStatus = {
  isActive: boolean;
  lastRunAt: string | null;
  nextRunAt: string | null;
  intervalMinutes: number;
  totalArticles: number;
  todayArticles: number;
  activeSources: number;
};

export type NewsStats = {
  totalArticles: number;
  todayArticles: number;
  activeSources: number;
  avgPerHour: number;
};
