import { spawn, ChildProcess } from "child_process";
import path from "path";
import { storage } from "./storage";

class ScraperScheduler {
  private intervalId: NodeJS.Timeout | null = null;
  private isRunning = false;
  private currentInterval = 0;
  private scraperProcess: ChildProcess | null = null;

  async start() {
    console.log("Starting scraper scheduler...");
    this.isRunning = true;
    await this.scheduleNext();
  }

  stop() {
    console.log("Stopping scraper scheduler...");
    this.isRunning = false;
    
    if (this.intervalId) {
      clearTimeout(this.intervalId);
      this.intervalId = null;
    }

    if (this.scraperProcess) {
      this.scraperProcess.kill();
      this.scraperProcess = null;
    }
  }

  async scheduleNext() {
    if (!this.isRunning) return;

    try {
      const config = await storage.getScraperConfig();
      
      if (!config.isActive) {
        // Check again in 30 seconds if scraper becomes active
        this.intervalId = setTimeout(() => this.scheduleNext(), 30000);
        return;
      }

      const intervalMs = config.intervalMinutes * 60 * 1000;
      
      // If interval changed, reschedule
      if (this.currentInterval !== config.intervalMinutes) {
        console.log(`Scraper interval updated to ${config.intervalMinutes} minutes`);
        this.currentInterval = config.intervalMinutes;
        
        if (this.intervalId) {
          clearTimeout(this.intervalId);
          this.intervalId = null;
        }
      }

      // Run scraper now
      await this.runScraper();

      // Schedule next run
      this.intervalId = setTimeout(() => this.scheduleNext(), intervalMs);
      
      const nextRun = new Date(Date.now() + intervalMs);
      console.log(`Next scraper run scheduled for: ${nextRun.toISOString()}`);

    } catch (error) {
      console.error("Error in scheduler:", error);
      // Retry in 1 minute if there's an error
      if (this.isRunning) {
        this.intervalId = setTimeout(() => this.scheduleNext(), 60000);
      }
    }
  }

  private async runScraper(): Promise<void> {
    return new Promise((resolve) => {
      console.log("Running scraper...");
      
      const pythonPath = path.join(process.cwd(), "server", "scraper_standalone.py");
      
      this.scraperProcess = spawn("python3", [pythonPath, "scrape"], {
        stdio: "pipe",
        cwd: process.cwd()
      });

      let output = "";
      
      this.scraperProcess.stdout?.on("data", (data) => {
        const text = data.toString();
        output += text;
        console.log("Scraper:", text.trim());
      });

      this.scraperProcess.stderr?.on("data", (data) => {
        console.error("Scraper error:", data.toString().trim());
      });

      this.scraperProcess.on("close", async (code) => {
        console.log(`Scraper process exited with code ${code}`);
        
        // Update last run time
        try {
          await storage.updateScraperConfig({ 
            lastRunAt: new Date() 
          });
        } catch (error) {
          console.error("Failed to update last run time:", error);
        }

        this.scraperProcess = null;
        resolve();
      });

      this.scraperProcess.on("error", (error) => {
        console.error("Failed to start scraper process:", error);
        this.scraperProcess = null;
        resolve();
      });
    });
  }

  async updateInterval(newIntervalMinutes: number) {
    console.log(`Updating scraper interval to ${newIntervalMinutes} minutes`);
    
    // Update the config
    await storage.updateScraperConfig({ 
      intervalMinutes: newIntervalMinutes 
    });

    // If scheduler is running, it will pick up the new interval on next cycle
    if (this.isRunning && this.currentInterval !== newIntervalMinutes) {
      // Force immediate reschedule with new interval
      if (this.intervalId) {
        clearTimeout(this.intervalId);
        this.intervalId = null;
      }
      
      // Schedule next run with new interval (don't run immediately)
      const intervalMs = newIntervalMinutes * 60 * 1000;
      this.currentInterval = newIntervalMinutes;
      
      this.intervalId = setTimeout(() => this.scheduleNext(), intervalMs);
      
      const nextRun = new Date(Date.now() + intervalMs);
      console.log(`Rescheduled next scraper run for: ${nextRun.toISOString()}`);
    }
  }

  isActive(): boolean {
    return this.isRunning;
  }

  getCurrentInterval(): number {
    return this.currentInterval;
  }
}

// Export singleton instance
export const scraperScheduler = new ScraperScheduler();