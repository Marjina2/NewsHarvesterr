import type { Express } from "express";
import { createServer, type Server } from "http";
import { storage } from "./storage";
import { insertNewsSourceSchema, insertNewsArticleSchema, updateScraperConfigSchema } from "@shared/schema";
import { z } from "zod";
import { spawn } from "child_process";
import path from "path";

export async function registerRoutes(app: Express): Promise<Server> {
  // Health check endpoint for Render
  app.get('/api/health', (_req, res) => {
    res.status(200).json({ 
      status: 'healthy', 
      timestamp: new Date().toISOString(),
      uptime: process.uptime(),
      version: '1.0.0'
    });
  });

  // Rate limiting map for authentication attempts
  const authAttempts = new Map<string, { count: number; lastAttempt: number }>();

  // Authentication middleware with rate limiting
  const requireAuth = (req: any, res: any, next: any) => {
    const clientIp = req.ip || req.connection.remoteAddress || 'unknown';
    const authToken = req.headers.authorization?.replace('Bearer ', '') || req.body.token;
    const masterToken = process.env.MASTER_TOKEN;
    
    if (!masterToken) {
      return res.status(500).json({ error: 'Server configuration error' });
    }

    // Rate limiting check
    const now = Date.now();
    const attempts = authAttempts.get(clientIp) || { count: 0, lastAttempt: 0 };
    
    // Reset counter if last attempt was more than 15 minutes ago
    if (now - attempts.lastAttempt > 15 * 60 * 1000) {
      attempts.count = 0;
    }

    // Block if too many failed attempts
    if (attempts.count >= 5) {
      return res.status(429).json({ error: 'Too many authentication attempts. Please try again later.' });
    }
    
    if (!authToken || authToken !== masterToken) {
      // Log failed attempt
      attempts.count++;
      attempts.lastAttempt = now;
      authAttempts.set(clientIp, attempts);
      
      return res.status(401).json({ error: 'Unauthorized access' });
    }
    
    // Reset attempts on successful auth
    authAttempts.delete(clientIp);
    next();
  };

  // Public auth endpoint
  app.post('/api/auth/verify', (req, res) => {
    const { token } = req.body;
    const masterToken = process.env.MASTER_TOKEN;
    
    if (!masterToken) {
      return res.status(500).json({ error: 'Server configuration error' });
    }
    
    if (token === masterToken) {
      res.json({ success: true, message: 'Authentication successful' });
    } else {
      res.status(401).json({ error: 'Invalid token' });
    }
  });
  // News Sources endpoints (protected)
  app.get("/api/sources", requireAuth, async (req, res) => {
    try {
      const sources = await storage.getNewsSources();
      res.json(sources);
    } catch (error) {
      res.status(500).json({ error: "Failed to fetch news sources" });
    }
  });

  app.post("/api/sources", requireAuth, async (req, res) => {
    try {
      const validatedData = insertNewsSourceSchema.parse(req.body);
      const source = await storage.createNewsSource(validatedData);
      res.json(source);
    } catch (error) {
      if (error instanceof z.ZodError) {
        res.status(400).json({ error: "Invalid data", details: error.errors });
      } else {
        res.status(500).json({ error: "Failed to create news source" });
      }
    }
  });

  app.delete("/api/sources/:id", requireAuth, async (req, res) => {
    try {
      const id = parseInt(req.params.id);
      await storage.deleteNewsSource(id);
      res.json({ success: true });
    } catch (error) {
      res.status(500).json({ error: "Failed to delete news source" });
    }
  });

  // News Articles endpoints (protected)
  app.get("/api/news", requireAuth, async (req, res) => {
    try {
      const limit = parseInt(req.query.limit as string) || 50;
      const offset = parseInt(req.query.offset as string) || 0;
      const articles = await storage.getNewsArticles(limit, offset);
      res.json(articles);
    } catch (error) {
      res.status(500).json({ error: "Failed to fetch news articles" });
    }
  });

  app.post("/api/articles", requireAuth, async (req, res) => {
    try {
      const validatedData = insertNewsArticleSchema.parse(req.body);
      const article = await storage.createNewsArticle(validatedData);
      res.json(article);
    } catch (error) {
      if (error instanceof z.ZodError) {
        res.status(400).json({ error: "Invalid data", details: error.errors });
      } else {
        res.status(500).json({ error: "Failed to create news article" });
      }
    }
  });

  app.get("/api/articles/pending", requireAuth, async (req, res) => {
    try {
      const articles = await storage.getNewsArticlesByStatus("pending");
      res.json(articles);
    } catch (error) {
      res.status(500).json({ error: "Failed to fetch pending articles" });
    }
  });

  app.put("/api/articles/:id", requireAuth, async (req, res) => {
    try {
      const id = parseInt(req.params.id);
      const { status, rephrasedTitle } = req.body;
      
      await storage.updateNewsArticleStatus(id, status, rephrasedTitle);
      res.json({ success: true });
    } catch (error) {
      res.status(500).json({ error: "Failed to update article status" });
    }
  });

  // All Articles JSON endpoint (must come before /:id route) (protected)
  app.get("/api/articles/all", requireAuth, async (req, res) => {
    try {
      const limit = parseInt(req.query.limit as string) || 1000; // Default to 1000 articles
      const articles = await storage.getNewsArticles(limit, 0);
      
      // Calculate trending status based on recency and category distribution
      const now = new Date();
      const categoryCount: Record<string, number> = {};
      const regionCount: Record<string, number> = {};
      
      // Count articles by category and region for trending calculation
      articles.forEach(article => {
        const category = article.category || 'general';
        const region = article.region || 'international';
        categoryCount[category] = (categoryCount[category] || 0) + 1;
        regionCount[region] = (regionCount[region] || 0) + 1;
      });
      
      // Return complete article details as JSON array
      const allArticles = articles.map((article, index) => {
        const scrapedDate = new Date(article.scrapedAt || now);
        const hoursOld = (now.getTime() - scrapedDate.getTime()) / (1000 * 60 * 60);
        const category = article.category || 'general';
        const region = article.region || 'international';
        
        // Simple trending algorithm: recent articles + category popularity + position
        const recencyScore = Math.max(0, 24 - hoursOld) / 24; // Higher score for newer articles
        const categoryPopularity = (categoryCount[category] || 1) / articles.length;
        const positionScore = Math.max(0, (50 - index) / 50); // Higher score for articles closer to top
        
        const trendingScore = (recencyScore * 0.4) + (categoryPopularity * 0.3) + (positionScore * 0.3);
        const isTrending = trendingScore > 0.5 && hoursOld < 12; // Trending if score > 0.5 and less than 12 hours old
        
        return {
          id: article.id,
          sourceName: article.sourceName,
          originalTitle: article.originalTitle,
          rephrasedTitle: article.rephrasedTitle,
          originalUrl: article.originalUrl,
          fullContent: article.fullContent,
          excerpt: article.excerpt,
          publishedAt: article.publishedAt,
          imageUrl: article.imageUrl,
          author: article.author,
          category: category,
          region: region,
          isTrending: isTrending,
          trendingScore: Math.round(trendingScore * 100) / 100, // Round to 2 decimal places
          status: article.status,
          scrapedAt: article.scrapedAt,
          rephrasedAt: article.rephrasedAt,
        };
      });
      
      // Sort by trending score for better organization
      const sortedArticles = allArticles.sort((a, b) => {
        if (a.isTrending && !b.isTrending) return -1;
        if (!a.isTrending && b.isTrending) return 1;
        return b.trendingScore - a.trendingScore;
      });
      
      // Generate summary statistics
      const trendingCount = sortedArticles.filter(a => a.isTrending).length;
      const categoriesBreakdown = Object.entries(categoryCount).map(([cat, count]) => ({
        category: cat,
        count,
        percentage: Math.round((count / articles.length) * 100)
      }));
      const regionsBreakdown = Object.entries(regionCount).map(([reg, count]) => ({
        region: reg,
        count,
        percentage: Math.round((count / articles.length) * 100)
      }));
      
      res.json({
        total: sortedArticles.length,
        trending: trendingCount,
        summary: {
          categories: categoriesBreakdown,
          regions: regionsBreakdown,
          trendingArticles: trendingCount
        },
        articles: sortedArticles
      });
    } catch (error) {
      res.status(500).json({ error: "Failed to fetch all articles" });
    }
  });

  app.get("/api/articles/:id", async (req, res) => {
    try {
      const id = parseInt(req.params.id);
      const articles = await storage.getNewsArticles(1, 0);
      const article = articles.find(a => a.id === id);
      
      if (!article) {
        return res.status(404).json({ error: "Article not found" });
      }
      
      res.json(article);
    } catch (error) {
      res.status(500).json({ error: "Failed to fetch article details" });
    }
  });

  app.get("/api/articles/:id/json", requireAuth, async (req, res) => {
    try {
      const id = parseInt(req.params.id);
      const articles = await storage.getNewsArticles(1000, 0); // Get all articles
      const article = articles.find(a => a.id === id);
      
      if (!article) {
        return res.status(404).json({ error: "Article not found" });
      }
      
      // Return complete article details as JSON
      const articleDetails = {
        id: article.id,
        sourceName: article.sourceName,
        originalTitle: article.originalTitle,
        rephrasedTitle: article.rephrasedTitle,
        originalUrl: article.originalUrl,
        fullContent: article.fullContent,
        excerpt: article.excerpt,
        publishedAt: article.publishedAt,
        imageUrl: article.imageUrl,
        author: article.author,
        status: article.status,
        scrapedAt: article.scrapedAt,
        rephrasedAt: article.rephrasedAt,
      };
      
      res.json(articleDetails);
    } catch (error) {
      res.status(500).json({ error: "Failed to fetch article JSON" });
    }
  });

  // Scraper Configuration endpoints (protected)
  app.get("/api/config", requireAuth, async (req, res) => {
    try {
      const config = await storage.getScraperConfig();
      res.json(config);
    } catch (error) {
      res.status(500).json({ error: "Failed to fetch scraper config" });
    }
  });

  app.post("/api/config", requireAuth, async (req, res) => {
    try {
      const validatedData = updateScraperConfigSchema.parse(req.body);
      const config = await storage.updateScraperConfig(validatedData);
      res.json(config);
    } catch (error) {
      if (error instanceof z.ZodError) {
        res.status(400).json({ error: "Invalid data", details: error.errors });
      } else {
        res.status(500).json({ error: "Failed to update scraper config" });
      }
    }
  });

  // Scraper Control endpoints (protected)
  app.post("/api/scraper/start", requireAuth, async (req, res) => {
    try {
      await storage.updateScraperConfig({ isActive: true });
      
      // Start Python scraper service
      const pythonPath = path.join(process.cwd(), "server", "main.py");
      const pythonProcess = spawn("python", [pythonPath, "start"], {
        stdio: "inherit",
        detached: true,
      });
      
      res.json({ success: true, message: "Scraper started successfully" });
    } catch (error) {
      res.status(500).json({ error: "Failed to start scraper" });
    }
  });

  app.post("/api/scraper/stop", requireAuth, async (req, res) => {
    try {
      await storage.updateScraperConfig({ isActive: false });
      
      // Stop Python scraper service
      const pythonPath = path.join(process.cwd(), "server", "main.py");
      const pythonProcess = spawn("python", [pythonPath, "stop"], {
        stdio: "inherit",
        detached: true,
      });
      
      res.json({ success: true, message: "Scraper stopped successfully" });
    } catch (error) {
      res.status(500).json({ error: "Failed to stop scraper" });
    }
  });

  app.post("/api/scraper/last-run", async (req, res) => {
    try {
      const config = await storage.getScraperConfig();
      await storage.updateScraperConfig({ 
        isActive: config.isActive,
        intervalMinutes: config.intervalMinutes 
      });
      res.json({ success: true });
    } catch (error) {
      res.status(500).json({ error: "Failed to update last run" });
    }
  });

  // Statistics endpoint (protected)
  app.get("/api/stats", requireAuth, async (req, res) => {
    try {
      const stats = await storage.getNewsStats();
      res.json(stats);
    } catch (error) {
      res.status(500).json({ error: "Failed to fetch statistics" });
    }
  });

  // Scraper Status endpoint
  app.get("/api/scraper/status", requireAuth, async (req, res) => {
    try {
      const config = await storage.getScraperConfig();
      const stats = await storage.getNewsStats();
      
      const nextRunAt = config.lastRunAt 
        ? new Date(config.lastRunAt.getTime() + config.intervalMinutes * 60000)
        : null;

      const status = {
        isActive: config.isActive,
        lastRunAt: config.lastRunAt?.toISOString() || null,
        nextRunAt: nextRunAt?.toISOString() || null,
        intervalMinutes: config.intervalMinutes,
        totalArticles: stats.totalArticles,
        todayArticles: stats.todayArticles,
        activeSources: stats.activeSources,
      };

      res.json(status);
    } catch (error) {
      res.status(500).json({ error: "Failed to fetch scraper status" });
    }
  });

  const httpServer = createServer(app);
  return httpServer;
}
