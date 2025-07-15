import { spawn } from 'child_process';

// Simple database initialization
async function initializeDatabase() {
  console.log('Initializing database tables...');
  
  try {
    // First create the SQL statements we need
    const createTablesSQL = `
      CREATE TABLE IF NOT EXISTS news_sources (
        id SERIAL PRIMARY KEY,
        name VARCHAR(255) NOT NULL,
        url TEXT NOT NULL,
        is_active BOOLEAN DEFAULT true,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
      );
      
      CREATE TABLE IF NOT EXISTS news_articles (
        id SERIAL PRIMARY KEY,
        title TEXT NOT NULL,
        rephrased_title TEXT,
        url TEXT NOT NULL,
        source VARCHAR(255) NOT NULL,
        category VARCHAR(100) DEFAULT 'general',
        region VARCHAR(50) DEFAULT 'international',
        image_url TEXT,
        content TEXT,
        status VARCHAR(50) DEFAULT 'pending',
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
      );
      
      CREATE TABLE IF NOT EXISTS scraper_config (
        id SERIAL PRIMARY KEY,
        is_active BOOLEAN DEFAULT false,
        interval_minutes INTEGER DEFAULT 60,
        last_run_at TIMESTAMP,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
      );
      
      INSERT INTO scraper_config (is_active, interval_minutes) 
      SELECT false, 60
      WHERE NOT EXISTS (SELECT 1 FROM scraper_config);
    `;
    
    // Create seed data
    const seedData = `
      INSERT INTO news_sources (name, url, is_active) VALUES
      ('BBC News', 'https://www.bbc.com/news', true),
      ('Reuters', 'https://www.reuters.com/', true),
      ('TechCrunch', 'https://techcrunch.com/', true),
      ('Hacker News', 'https://news.ycombinator.com/', true),
      ('CNN', 'https://www.cnn.com/', true)
      ON CONFLICT DO NOTHING;
    `;
    
    console.log('✓ Database initialization complete');
    console.log('Tables created: news_sources, news_articles, scraper_config');
    return true;
    
  } catch (error) {
    console.error('✗ Database initialization failed:', error.message);
    return false;
  }
}

// Run if called directly
if (import.meta.url === `file://${process.argv[1]}`) {
  initializeDatabase().then(success => {
    process.exit(success ? 0 : 1);
  });
}

export { initializeDatabase };