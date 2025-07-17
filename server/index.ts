import express from "express";
import { spawn } from "child_process";
import path from "path";
import { registerRoutes } from "./routes";
import { createServer } from "http";
import { fileURLToPath } from "url";

const __filename = fileURLToPath(import.meta.url);
const __dirname = path.dirname(__filename);

const app = express();
const port = process.env.PORT || 5000;

// Parse JSON bodies
app.use(express.json());

// In production, serve static files from dist/public
if (process.env.NODE_ENV === 'production') {
  const staticPath = path.join(__dirname, 'public');
  app.use(express.static(staticPath));

  // Serve index.html for all non-API routes (SPA routing)
  app.get('*', (req, res, next) => {
    if (req.path.startsWith('/api')) {
      return next();
    }
    res.sendFile(path.join(staticPath, 'index.html'));
  });
} else {
  // In development, provide a helpful message for root route
  app.get('/', (req, res) => {
    res.json({
      message: 'News Scraper API Server',
      status: 'running',
      environment: 'development',
      frontend_url: 'Open the frontend in a new tab or use the webview',
      api_health: '/api/health',
      documentation: 'Check README.md for API endpoints'
    });
  });
}

// Register API routes
const server = await registerRoutes(app);

server.listen(port, '0.0.0.0', () => {
  console.log(`Server running on port ${port}`);
});

// Start Python scheduler in background
if (process.env.NODE_ENV === 'production') {
  console.log('Attempting to start Python scheduler...');
  const pythonProcess = spawn('python3', [path.join(__dirname, '..', 'server', 'main.py'), 'start'], {
    stdio: 'inherit',
    cwd: path.join(__dirname, '..', 'server')
  });

  pythonProcess.on('error', (error) => {
    console.error('Failed to start Python scheduler:', error);
    console.log('Python scheduler disabled - web scraping will not be available');
  });

  pythonProcess.on('exit', (code) => {
    if (code !== 0) {
      console.error(`Python scheduler exited with code ${code}`);
      console.log('Python scheduler disabled - web scraping will not be available');
    }
  });
} else {
  console.log('Development mode - Python scheduler not started');
}