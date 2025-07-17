import express from "express";
import { spawn } from "child_process";
import path from "path";
import { registerRoutes } from "./routes";
import { createServer } from "http";
import { fileURLToPath } from "url";
import { exec } from "child_process";
import { promisify } from "util";

const __filename = fileURLToPath(import.meta.url);
const __dirname = path.dirname(__filename);

const execAsync = promisify(exec);

// Install Python requirements on startup (non-blocking)
function installPythonRequirements() {
  exec('pip install -r requirements.txt', (error, stdout, stderr) => {
    if (error) {
      console.log('Note: Python requirements installation failed or already installed');
    } else {
      console.log('Python requirements installed successfully');
    }
  });
}

// Install requirements in background (non-blocking)
installPythonRequirements();

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
}

// Register API routes
const server = await registerRoutes(app);

server.listen(port, '0.0.0.0', () => {
  console.log(`Server running on port ${port}`);
});

// Start Python scheduler in background
if (process.env.NODE_ENV === 'production') {
  console.log('Attempting to start Python scheduler...');
  const pythonProcess = spawn('python3', [path.join(__dirname, '..', 'server', 'scraper_standalone.py'), 'start'], {
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