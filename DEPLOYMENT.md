# Render Deployment Guide

## Pre-deployment Checklist

### 1. Environment Variables Required
Set these in your Render dashboard:

```env
# Database (Required)
DATABASE_URL=postgresql://username:password@host:port/database

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

**CRITICAL**: The DATABASE_URL must be a valid PostgreSQL connection string. The application has been fixed to properly use this variable for all database connections.

### Step 4: Database Migration
After first deployment, run:
```bash
npm run db:push
```

## Health Check
The app includes a health check endpoint at `/api/health` for monitoring.

## Troubleshooting

### Common Issues

**Build Failures**
- Ensure Node.js 18+ is selected
- Check build logs for missing dependencies
- Verify package.json scripts are correct

**Database Connection**
- Verify DATABASE_URL format: `postgresql://user:pass@host:port/db`
- Check database is accessible from Render  
- Run database migrations after deployment
- **FIXED**: Removed hardcoded Supabase error that was blocking deployment

**Authentication Issues**
- Ensure MASTER_TOKEN is set in environment variables
- Token should be at least 32 characters long
- All API endpoints are now protected with authentication

**Python Dependencies**
- Python services run as child processes
- Ensure all Python packages are in requirements.txt
- Check Python version compatibility

### Performance Optimization
- Use Render's auto-scaling features
- Enable CDN for static assets
- Monitor memory usage and upgrade plan if needed

## Post-Deployment

### 1. Verify Health
Visit: `https://your-app.onrender.com/api/health`

### 2. Test Core Functions
- Dashboard loads correctly
- News sources can be added
- Scraper can be started/stopped
- Articles display properly

### 3. Monitor Logs
Check Render logs for any runtime errors or warnings.

## Production Configuration

### Database
- Use Render PostgreSQL for production
- Enable automated backups
- Set appropriate connection limits

### Security
- All API keys stored as environment variables
- CORS configured for production domain
- Input validation on all endpoints

### Monitoring
- Health check endpoint for uptime monitoring
- Error tracking and logging
- Performance metrics collection

## Scaling Considerations

### Performance
- Current setup handles ~1000 articles efficiently
- Scraping runs in background processes
- Database optimized with indexes

### Limits
- Render free tier: 750 hours/month
- Database connections: Monitor usage
- Memory: 512MB default (upgrade if needed)

## Support

For deployment issues:
1. Check Render build logs
2. Verify environment variables
3. Test database connectivity
4. Review application logs

## Useful Commands

```bash
# Local testing of production build
npm run build
npm start

# Database operations
npm run db:push
npm run db:studio

# Check logs
render logs --service your-service-name
```