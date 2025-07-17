# Render Deployment Fix

## Issue
The deployment logs show that the Python requirements are being installed correctly, but the deployment is failing because:

1. The build command is using `pip install -r requirements.txt && npm run dev`
2. `npm run dev` is a development command, not suitable for production
3. The port detection is failing because dev server doesn't bind to the correct port

## Solution

### 1. Updated render.yaml
- Changed environment from `python` to `node`
- Fixed start command to use `npm start` instead of development server
- Added proper PORT environment variable

### 2. Production Build Process
The correct build and start commands should be:
- **Build**: `npm install && npm run build`
- **Start**: `npm start`

### 3. Key Changes Made
1. Environment: `node` (not python)
2. Start command: `npm start` (not `npm run dev`)
3. Added PORT=10000 environment variable
4. Fixed service name to `news-scraper-dashboard`

## Next Steps for Deployment
1. Push these changes to your GitHub repository
2. In Render dashboard, update the service configuration:
   - Environment: Node
   - Build Command: `npm install && npm run build`
   - Start Command: `npm start`
3. Add environment variables:
   - DATABASE_URL (your PostgreSQL connection string)
   - MASTER_TOKEN (your authentication token)
   - NODE_ENV=production
   - PORT=10000

## Why This Works
- Node.js environment handles both frontend and backend
- Python requirements are installed during build phase
- Production server (npm start) binds to proper port
- Static files are served from dist/public folder