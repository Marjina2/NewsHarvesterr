# News Scraper Dashboard

## Overview

This is a full-stack news scraper application that automatically collects news articles from various sources and uses AI to rephrase headlines. The system consists of a React frontend with a Node.js/Express backend, PostgreSQL database, and Python-based scraping services.

## User Preferences

Preferred communication style: Simple, everyday language.

## Recent Changes: Latest modifications with dates

### Comprehensive Documentation & Final Polish - July 13, 2025
- ✅ **Created Detailed README**: Comprehensive documentation with architecture, setup, and usage guides
- ✅ **Fixed Duplicate Articles**: Removed 176 duplicate articles and enhanced duplicate detection system
- ✅ **Enhanced Image Handling**: All articles now have proper images (real images + branded placeholders)
- ✅ **Improved Content Quality**: Enhanced full article extraction with better timeout and NLP processing
- ✅ **Optimized Pagination**: Updated to show 20 articles per page with improved performance

### Supabase Migration & 20 News Sources - July 13, 2025
- ✅ **Migrated to Supabase**: Successfully configured database to use Supabase instead of Neon
- ✅ **Added 20 Comprehensive News Sources**: Includes international, technology, Indian, and business news
- ✅ **Fixed Python Dependencies**: Installed all required scraping libraries
- ✅ **Database Schema Applied**: All tables properly created in Supabase
- ✅ **Environment Configuration**: Set up SUPABASE_URL and SUPABASE_ANON_KEY secrets

### Category Filtration & Indian News Sources - July 13, 2025
- ✅ **Added Category Filtration**: Articles now categorized into Technology, Business, Politics, Sports, Science, Entertainment, and General
- ✅ **Added Region Classification**: Articles classified as Indian or International news
- ✅ **Enhanced Scraper**: Modified scraper to collect 10 Indian-specific + 10 international articles per source (20 total)
- ✅ **Added Indian News Sources**: Added India Today, NDTV, Times of India, Hindu, and Economic Times
- ✅ **Updated Database Schema**: Added category and region fields to articles table
- ✅ **Enhanced Frontend**: Added category and region filters in the news display interface
- ✅ **Intelligent Classification**: AI-powered categorization based on article content and keywords
- ✅ **Visual Indicators**: Added colored badges for categories and regions with emojis

## System Architecture

### Frontend Architecture
- **Framework**: React 18 with TypeScript
- **Build Tool**: Vite for fast development and optimized builds
- **UI Framework**: Tailwind CSS with shadcn/ui components
- **State Management**: TanStack React Query for server state management
- **Routing**: Wouter for lightweight client-side routing
- **Styling**: Tailwind CSS with CSS variables for theming

### Backend Architecture
- **Runtime**: Node.js with Express.js framework
- **Language**: TypeScript with ES modules
- **Database ORM**: Drizzle ORM for type-safe database operations
- **Database**: PostgreSQL (configured for Neon serverless)
- **Validation**: Zod for runtime type validation
- **Process Management**: Child processes for Python scraper integration

### Scraping Services
- **Language**: Python 3
- **Web Scraping**: BeautifulSoup for HTML parsing
- **HTTP Client**: Requests library for web requests
- **Scheduling**: Python schedule library for periodic tasks
- **AI Integration**: OpenRouter API with Mistral AI for headline rephrasing

## Key Components

### Database Schema
The application uses three main tables:
- `news_sources`: Stores news website URLs and metadata
- `news_articles`: Stores scraped articles with original and rephrased titles
- `scraper_config`: Stores scraper settings and status

### API Endpoints
- `/api/sources`: CRUD operations for news sources
- `/api/news`: Retrieve news articles with pagination
- `/api/config`: Scraper configuration management
- `/api/scraper/start|stop`: Control scraper execution
- `/api/stats`: Dashboard statistics

### Frontend Components
- **Dashboard**: Main application view with status indicators
- **NewsDisplay**: Article listing with filtering and pagination
- **NewsSourcesManager**: Add/remove news sources
- **ScraperControls**: Start/stop scraper and adjust settings
- **StatisticsPanel**: Real-time scraping statistics

## Data Flow

1. **User Configuration**: Users add news sources through the web interface
2. **Scheduled Scraping**: Python services run on configurable intervals
3. **Article Storage**: Scraped articles are stored in PostgreSQL
4. **AI Processing**: Headlines are sent to OpenRouter/Mistral for rephrasing
5. **Real-time Updates**: Frontend polls for new articles and status updates

## External Dependencies

### Required Services
- **PostgreSQL Database**: For persistent data storage
- **OpenRouter API**: For AI-powered headline rephrasing
- **Python Runtime**: For scraping services

### Key NPM Packages
- `@tanstack/react-query`: Server state management
- `drizzle-orm`: Database ORM
- `@radix-ui/*`: UI component primitives
- `wouter`: Lightweight routing
- `zod`: Runtime validation

### Python Dependencies
- `requests`: HTTP client for web scraping
- `beautifulsoup4`: HTML parsing
- `schedule`: Task scheduling

## Deployment Strategy

The application is designed for Replit deployment with:
- **Development**: `npm run dev` starts both frontend and backend
- **Production**: `npm run build` creates optimized bundles
- **Database**: Drizzle migrations with PostgreSQL
- **Environment**: Requires `DATABASE_URL` and `OPENROUTER_API_KEY`

### Build Process
1. Frontend builds to `dist/public` using Vite
2. Backend compiles to `dist/index.js` using esbuild
3. Python services run independently via Node.js child processes
4. Database migrations run via `npm run db:push`

### Configuration
- Drizzle config points to `shared/schema.ts`
- Tailwind processes `client/src/index.css`
- TypeScript paths configured for `@/*` and `@shared/*` aliases
- Vite dev server proxies API calls to Express backend