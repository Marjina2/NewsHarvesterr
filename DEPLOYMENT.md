# Render Deployment Guide

## Pre-deployment Checklist

### 1. Environment Variables Required
Set these in your Render dashboard:

```env
# Database (Required)
DATABASE_URL=postgresql://username:password@host:port/database

# Authentication (Required)
MASTER_TOKEN=your_secure_master_token_32_chars_minimum

# Optional - For AI headline rephrasing
OPENROUTER_API_KEY=your_openrouter_api_key

# Auto-set by Render
NODE_ENV=production
PORT=10000
```

### 2. PostgreSQL Database Setup
1. Create a PostgreSQL database on Render
2. Copy the connection string from database dashboard
3. Use it as DATABASE_URL environment variable

### 3. Build Configuration
- **Build Command**: `npm install && npm run build`
- **Start Command**: `npm start`
- **Node Version**: 18.x or higher

## Deployment Steps

### Step 1: Connect Repository
1. Go to [Render Dashboard](https://dashboard.render.com)
2. Click "New +" → "Web Service"
3. Connect your GitHub repository

### Step 2: Configure Service
```yaml
Name: news-scraper-dashboard
Environment: Node
Region: Choose closest to your users
Branch: main
Build Command: npm install && npm run build
Start Command: npm start
```

### Step 3: Environment Variables
Add these environment variables in Render dashboard:
- `DATABASE_URL` - Your PostgreSQL connection string (**REQUIRED**)
- `MASTER_TOKEN` - Your secure authentication token (**REQUIRED**)
- `OPENROUTER_API_KEY` - (Optional) For AI features
- `NODE_ENV` - Set to "production"

**CRITICAL**: The DATABASE_URL must be a valid PostgreSQL connection string.

### Step 4: Database Migration
After first deployment, run database setup:
```bash
# The app will automatically create tables on first run
# No manual migration needed
```

## Health Check
The app includes a health check endpoint at `/api/health` for monitoring.

## Post-Deployment Verification

### Health Checks
- [ ] `/api/health` returns 200 status
- [ ] Dashboard loads at root URL
- [ ] API endpoints respond correctly

### Functionality Tests
- [ ] News articles display properly
- [ ] Pagination works (20 articles per page)
- [ ] Category and region filters function
- [ ] Images load correctly
- [ ] Scraper controls work
- [ ] Sources can be managed

## Troubleshooting

### Common Issues

**Build Failures**
- Ensure Node.js 18+ is selected
- Check build logs for missing dependencies
- Verify package.json scripts are correct

**Database Connection**
- Verify DATABASE_URL format: `postgresql://user:pass@host:port/db`
- Check database is accessible from Render  
- Database tables are created automatically on first run

**Authentication Issues**
- Ensure MASTER_TOKEN is set in environment variables
- Token should be at least 32 characters long
- All API endpoints are protected with authentication

**Static File Serving**
- Production build serves files from dist/public/
- SPA routing handled automatically
- API routes preserved under /api/*

### Performance Optimization
- Use Render's auto-scaling features
- Monitor memory usage and upgrade plan if needed
- Database connection pooling included

## Production Configuration

### Security
- All API keys stored as environment variables
- Authentication required for all API endpoints
- Input validation on all endpoints

### Monitoring
- Health check endpoint for uptime monitoring
- Console logging for debugging
- Database connection status monitoring

## Useful Commands

```bash
# Local testing of production build
npm run build
npm start

# Database operations
npm run db:push

# Check logs on Render
# View in Render dashboard logs section