# News Scraper Dashboard

A comprehensive news aggregation and analysis platform that collects, scrapes, and processes news articles from multiple international sources with AI-powered content processing.

![News Scraper Dashboard](https://via.placeholder.com/800x400/0066cc/ffffff?text=News+Scraper+Dashboard)

## 🌟 Features

### Core Functionality
- **Multi-Source Scraping**: Automated collection from 20+ premium news sources
- **AI-Powered Processing**: Intelligent headline rephrasing using advanced language models
- **Real-time Dashboard**: Live monitoring of scraping progress and article statistics
- **Smart Categorization**: Automatic classification into Technology, Business, Politics, Sports, Science, Entertainment, and General
- **Regional Classification**: Indian vs International content detection
- **Full Content Extraction**: Complete article text with images and metadata
- **Duplicate Prevention**: Advanced duplicate detection and removal system
- **Responsive Design**: Modern, mobile-friendly interface with dark mode support

### Advanced Features
- **Scheduled Scraping**: Configurable intervals with automatic execution
- **Image Processing**: Multi-fallback image extraction with branded placeholders
- **Category Filtering**: Filter articles by category, region, and processing status
- **Pagination**: Efficient browsing with 20 articles per page
- **Export Functionality**: Download articles in JSON format
- **Real-time Statistics**: Live updates on article counts and source activity

## 🏗️ Architecture

### Technology Stack
- **Frontend**: React 18 + TypeScript + Vite
- **Backend**: Node.js + Express.js + TypeScript
- **Database**: PostgreSQL (Supabase)
- **Scraping Engine**: Python 3 + BeautifulSoup + newspaper3k
- **UI Framework**: Tailwind CSS + shadcn/ui components
- **State Management**: TanStack React Query
- **ORM**: Drizzle ORM with type-safe operations

### System Components

```
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   React Frontend │    │  Express Backend │    │ Python Scrapers │
│                 │    │                 │    │                 │
│ • Dashboard     │◄──►│ • REST API      │◄──►│ • News Sources  │
│ • Article View  │    │ • WebSocket     │    │ • Content Extract│
│ • Filters       │    │ • Auth          │    │ • AI Processing │
└─────────────────┘    └─────────────────┘    └─────────────────┘
         │                       │                       │
         │                       │                       │
         └───────────────────────┼───────────────────────┘
                                 │
                    ┌─────────────────┐
                    │ PostgreSQL DB   │
                    │                 │
                    │ • Articles      │
                    │ • Sources       │
                    │ • Config        │
                    └─────────────────┘
```

## 🚀 Quick Start

### Prerequisites
- Node.js 18+ 
- Python 3.9+
- PostgreSQL database (Supabase recommended)
- Git

### Installation

1. **Clone the repository**
   ```bash
   git clone https://github.com/your-username/news-scraper-dashboard.git
   cd news-scraper-dashboard
   ```

2. **Install dependencies**
   ```bash
   npm install
   pip install -r requirements.txt
   ```

3. **Environment Setup**
   Create a `.env` file in the root directory:
   ```env
   DATABASE_URL=your_postgresql_connection_string
   SUPABASE_URL=your_supabase_project_url
   SUPABASE_ANON_KEY=your_supabase_anon_key
   OPENROUTER_API_KEY=your_openrouter_api_key
   NODE_ENV=development
   ```

4. **Database Setup**
   ```bash
   npm run db:push
   ```

5. **Start the application**
   ```bash
   npm run dev
   ```

   The application will be available at `http://localhost:5000`

## 📊 News Sources

The platform currently scrapes from 20 carefully selected sources:

### International Sources
- **BBC News** - Global news coverage
- **CNN** - Breaking news and analysis
- **Reuters** - International wire service
- **The Guardian** - UK-based global news
- **NPR** - Public radio news
- **Associated Press** - Wire service news

### Technology Sources
- **TechCrunch** - Startup and tech news
- **The Verge** - Technology and culture
- **Engadget** - Consumer technology
- **Ars Technica** - Technology analysis
- **WIRED** - Technology and innovation
- **Hacker News** - Tech community news

### Indian Sources
- **India Today** - National news
- **NDTV** - Breaking news India
- **Times of India** - Leading daily
- **The Hindu** - National newspaper
- **Economic Times** - Business news

### Business Sources
- **Financial Times** - Global business
- **Bloomberg** - Financial markets
- **Wall Street Journal** - Business news

## 🔧 Configuration

### Scraper Settings
Configure scraping behavior through the dashboard:
- **Interval**: Set scraping frequency (5-60 minutes)
- **Sources**: Enable/disable specific news sources
- **Categories**: Target article distribution per category

### Database Schema
The application uses three main tables:

```sql
-- News Sources
CREATE TABLE news_sources (
  id SERIAL PRIMARY KEY,
  name VARCHAR(255) NOT NULL,
  url TEXT NOT NULL,
  is_active BOOLEAN DEFAULT true,
  created_at TIMESTAMP DEFAULT NOW()
);

-- News Articles
CREATE TABLE news_articles (
  id SERIAL PRIMARY KEY,
  source_name VARCHAR(255),
  original_title TEXT NOT NULL,
  rephrased_title TEXT,
  original_url TEXT,
  full_content TEXT,
  excerpt TEXT,
  image_url TEXT,
  author VARCHAR(255),
  published_at TIMESTAMP,
  scraped_at TIMESTAMP DEFAULT NOW(),
  category VARCHAR(50) DEFAULT 'general',
  region VARCHAR(20) DEFAULT 'international',
  status VARCHAR(20) DEFAULT 'pending'
);

-- Scraper Configuration
CREATE TABLE scraper_config (
  id SERIAL PRIMARY KEY,
  interval_minutes INTEGER DEFAULT 15,
  is_active BOOLEAN DEFAULT false,
  last_run_at TIMESTAMP,
  created_at TIMESTAMP DEFAULT NOW()
);
```

## 🤖 AI Integration

### Headline Rephrasing
The system uses OpenRouter API with Mistral AI for intelligent headline rephrasing:
- **Original preservation**: Maintains original headlines
- **Enhanced readability**: Creates more engaging versions
- **Context awareness**: Considers source and content type
- **Batch processing**: Efficient API usage

### Content Categorization
Advanced categorization using:
- **Keyword analysis**: Weighted scoring system
- **Source-based classification**: Automatic tech/business detection
- **Content analysis**: Full article text consideration
- **Regional detection**: India-specific content identification

## 📱 Frontend Features

### Dashboard Components
- **Statistics Panel**: Real-time metrics and performance indicators
- **News Sources Manager**: Add, remove, and configure sources
- **Scraper Controls**: Start, stop, and schedule operations
- **News Display**: Paginated article browsing with filters

### User Interface
- **Responsive Design**: Mobile-first approach
- **Dark Mode**: System preference detection
- **Loading States**: Skeleton screens and progress indicators
- **Error Handling**: Graceful failure management
- **Real-time Updates**: Live data synchronization

## 🔒 Security & Performance

### Security Features
- **Environment Variables**: Secure API key management
- **CORS Protection**: Cross-origin request filtering
- **Input Validation**: Zod schema validation
- **Error Boundaries**: React error containment

### Performance Optimizations
- **Database Indexing**: Optimized query performance
- **Image Lazy Loading**: Progressive image loading
- **API Caching**: TanStack Query caching
- **Bundle Optimization**: Vite build optimizations
- **Concurrent Processing**: Multi-threaded scraping

## 🔄 Data Flow

### Scraping Process
1. **Source Activation**: Check active sources in database
2. **Content Extraction**: Fetch and parse article content
3. **Duplicate Detection**: Prevent duplicate articles
4. **Categorization**: Apply ML-based classification
5. **Storage**: Save to PostgreSQL database
6. **AI Processing**: Queue for headline rephrasing

### Real-time Updates
1. **Frontend Polling**: Periodic data refresh
2. **WebSocket Events**: Live status updates
3. **Cache Invalidation**: Smart cache management
4. **State Synchronization**: Consistent UI state

## 🚀 Deployment

### Production Deployment
1. **Build the application**
   ```bash
   npm run build
   ```

2. **Set production environment variables**
   ```env
   NODE_ENV=production
   DATABASE_URL=your_production_db_url
   PORT=3000
   ```

3. **Deploy to your platform**
   - **Replit Deployments**: Automatic deployment
   - **Vercel**: Frontend deployment
   - **Railway**: Full-stack deployment
   - **Docker**: Containerized deployment

### Environment Variables
| Variable | Description | Required |
|----------|-------------|----------|
| `DATABASE_URL` | PostgreSQL connection string | Yes |
| `SUPABASE_URL` | Supabase project URL | Yes |
| `SUPABASE_ANON_KEY` | Supabase anonymous key | Yes |
| `OPENROUTER_API_KEY` | OpenRouter API key for AI | No |
| `NODE_ENV` | Environment mode | Yes |
| `PORT` | Server port | No |

## 📈 Monitoring & Analytics

### Performance Metrics
- **Scraping Success Rate**: Article extraction success
- **Processing Speed**: Articles per minute
- **Error Rates**: Failed requests and timeouts
- **Storage Usage**: Database growth tracking

### Dashboard Analytics
- **Article Statistics**: Total, daily, and hourly counts
- **Source Performance**: Individual source metrics
- **Category Distribution**: Content type breakdown
- **Processing Status**: AI rephrasing progress

## 🛠️ Development

### Project Structure
```
news-scraper-dashboard/
├── client/                 # React frontend
│   ├── src/
│   │   ├── components/     # UI components
│   │   ├── hooks/          # Custom React hooks
│   │   ├── lib/           # Utilities and config
│   │   └── pages/         # Route components
├── server/                 # Node.js backend
│   ├── services/          # Python scraping services
│   ├── db.ts             # Database configuration
│   ├── routes.ts         # API endpoints
│   └── storage.ts        # Data access layer
├── shared/                # Shared TypeScript types
│   └── schema.ts         # Database schema
└── docs/                 # Documentation
```

### API Endpoints
- `GET /api/news` - Fetch articles with pagination
- `GET /api/sources` - Get news sources
- `POST /api/sources` - Add new source
- `GET /api/stats` - Dashboard statistics
- `POST /api/scraper/start` - Start scraping
- `POST /api/scraper/stop` - Stop scraping
- `GET /api/config` - Get scraper configuration

### Contributing
1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

## 🐛 Troubleshooting

### Common Issues

**Database Connection Issues**
```bash
# Check connection
psql $DATABASE_URL

# Reset database
npm run db:reset
```

**Scraping Failures**
```bash
# Check Python dependencies
pip install -r requirements.txt

# Test individual scraper
python server/services/scraper.py
```

**Build Errors**
```bash
# Clear cache
rm -rf node_modules package-lock.json
npm install

# Reset build
rm -rf dist
npm run build
```

### Logs and Debugging
- **Frontend**: Browser console for React errors
- **Backend**: Server logs for API issues
- **Scraper**: Python logs for extraction problems
- **Database**: PostgreSQL logs for query issues

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## 🤝 Support

For support and questions:
- **Issues**: GitHub Issues for bug reports
- **Discussions**: GitHub Discussions for questions
- **Email**: your-email@example.com

## 🙏 Acknowledgments

- **OpenRouter**: AI API services
- **Supabase**: Database hosting
- **shadcn/ui**: Component library
- **Replit**: Development platform
- **TanStack**: React Query library

## 📚 Additional Resources

- [API Documentation](docs/api.md)
- [Deployment Guide](docs/deployment.md)
- [Contributing Guidelines](CONTRIBUTING.md)
- [Changelog](CHANGELOG.md)

---

**Built with ❤️ using React, Node.js, and Python**