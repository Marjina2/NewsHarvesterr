import type { Express } from "express";
import { createServer, type Server } from "http";
import { storage } from "./storage";
import { insertNewsSourceSchema, insertNewsArticleSchema, updateScraperConfigSchema } from "@shared/schema";
import { z } from "zod";
import { spawn } from "child_process";
import path from "path";

export async function registerRoutes(app: Express): Promise<Server> {
  // News Sources endpoints
  app.get("/api/sources", async (req, res) => {
    try {
      const sources = await storage.getNewsSources();
      res.json(sources);
    } catch (error) {
      res.status(500).json({ error: "Failed to fetch news sources" });
    }
  });

  app.post("/api/sources", async (req, res) => {
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

  app.delete("/api/sources/:id", async (req, res) => {
    try {
      const id = parseInt(req.params.id);
      await storage.deleteNewsSource(id);
      res.json({ success: true });
    } catch (error) {
      res.status(500).json({ error: "Failed to delete news source" });
    }
  });

  // News Articles endpoints
  app.get("/api/news", async (req, res) => {
    try {
      const limit = parseInt(req.query.limit as string) || 50;
      const offset = parseInt(req.query.offset as string) || 0;
      const articles = await storage.getNewsArticles(limit, offset);
      res.json(articles);
    } catch (error) {
      res.status(500).json({ error: "Failed to fetch news articles" });
    }
  });

  app.post("/api/articles", async (req, res) => {
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

  app.get("/api/articles/pending", async (req, res) => {
    try {
      const articles = await storage.getNewsArticlesByStatus("pending");
      res.json(articles);
    } catch (error) {
      res.status(500).json({ error: "Failed to fetch pending articles" });
    }
  });

  app.put("/api/articles/:id", async (req, res) => {
    try {
      const id = parseInt(req.params.id);
      const { status, rephrasedTitle } = req.body;
      
      await storage.updateNewsArticleStatus(id, status, rephrasedTitle);
      res.json({ success: true });
    } catch (error) {
      res.status(500).json({ error: "Failed to update article status" });
    }
  });

  // Scraper Configuration endpoints
  app.get("/api/config", async (req, res) => {
    try {
      const config = await storage.getScraperConfig();
      res.json(config);
    } catch (error) {
      res.status(500).json({ error: "Failed to fetch scraper config" });
    }
  });

  app.post("/api/config", async (req, res) => {
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

  // Scraper Control endpoints
  app.post("/api/scraper/start", async (req, res) => {
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

  app.post("/api/scraper/stop", async (req, res) => {
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

  // Statistics endpoint
  app.get("/api/stats", async (req, res) => {
    try {
      const stats = await storage.getNewsStats();
      res.json(stats);
    } catch (error) {
      res.status(500).json({ error: "Failed to fetch statistics" });
    }
  });

  // Scraper Status endpoint
  app.get("/api/scraper/status", async (req, res) => {
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
