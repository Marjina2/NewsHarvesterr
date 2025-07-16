import { Pool } from 'pg';

const databaseUrl = process.env.DATABASE_URL;

if (!databaseUrl) {
  console.error('DATABASE_URL not found');
  process.exit(1);
}

const pool = new Pool({
  connectionString: databaseUrl,
  ssl: databaseUrl.includes('localhost') ? false : { rejectUnauthorized: false },
});

async function createTables() {
  try {
    console.log('Creating tables...');
    
    // Create news_sources table
    await pool.query(`
      CREATE TABLE IF NOT EXISTS news_sources (
        id SERIAL PRIMARY KEY,
        name TEXT NOT NULL,
        url TEXT NOT NULL UNIQUE,
        is_active BOOLEAN DEFAULT true,
        created_at TIMESTAMP DEFAULT NOW()
      );
    `);
    
    // Create news_articles table
    await pool.query(`
      CREATE TABLE IF NOT EXISTS news_articles (
        id SERIAL PRIMARY KEY,
        source_id INTEGER REFERENCES news_sources(id),
        source_name TEXT NOT NULL,
        original_title TEXT NOT NULL,
        rephrased_title TEXT,
        original_url TEXT,
        full_content TEXT,
        excerpt TEXT,
        published_at TIMESTAMP,
        image_url TEXT,
        author TEXT,
        category TEXT DEFAULT 'general',
        region TEXT DEFAULT 'international',
        status TEXT NOT NULL DEFAULT 'pending',
        scraped_at TIMESTAMP DEFAULT NOW(),
        rephrased_at TIMESTAMP
      );
    `);
    
    // Create scraper_config table
    await pool.query(`
      CREATE TABLE IF NOT EXISTS scraper_config (
        id SERIAL PRIMARY KEY,
        interval_minutes INTEGER NOT NULL DEFAULT 20,
        is_active BOOLEAN DEFAULT false,
        last_run_at TIMESTAMP,
        indian_articles_per_source INTEGER NOT NULL DEFAULT 10,
        international_articles_per_source INTEGER NOT NULL DEFAULT 10,
        extract_full_content BOOLEAN NOT NULL DEFAULT true,
        enable_categorization BOOLEAN NOT NULL DEFAULT true,
        updated_at TIMESTAMP DEFAULT NOW()
      );
    `);
    
    // Create indexes
    await pool.query(`
      CREATE INDEX IF NOT EXISTS scraped_at_idx ON news_articles(scraped_at);
      CREATE INDEX IF NOT EXISTS status_idx ON news_articles(status);
    `);
    
    console.log('Tables created successfully!');
    
    // Insert default scraper config if none exists
    const configResult = await pool.query('SELECT COUNT(*) FROM scraper_config');
    if (parseInt(configResult.rows[0].count) === 0) {
      await pool.query(`
        INSERT INTO scraper_config (interval_minutes, is_active, indian_articles_per_source, international_articles_per_source, extract_full_content, enable_categorization)
        VALUES (20, false, 10, 10, true, true)
      `);
      console.log('Default scraper config inserted');
    }
    
    // Insert default news sources if none exist
    const sourcesResult = await pool.query('SELECT COUNT(*) FROM news_sources');
    if (parseInt(sourcesResult.rows[0].count) === 0) {
      const defaultSources = [
        { name: "BBC News", url: "https://www.bbc.com/news" },
        { name: "Reuters", url: "https://www.reuters.com" },
        { name: "TechCrunch", url: "https://techcrunch.com" },
        { name: "Hacker News", url: "https://news.ycombinator.com" },
        { name: "CNN", url: "https://www.cnn.com" },
        { name: "The Guardian", url: "https://www.theguardian.com" },
        { name: "NPR", url: "https://www.npr.org" },
        { name: "Associated Press", url: "https://apnews.com" },
        { name: "India Today", url: "https://www.indiatoday.in" },
        { name: "NDTV", url: "https://www.ndtv.com" },
        { name: "Times of India", url: "https://timesofindia.indiatimes.com" },
        { name: "The Hindu", url: "https://www.thehindu.com" },
        { name: "Economic Times", url: "https://economictimes.indiatimes.com" },
        { name: "WIRED", url: "https://www.wired.com" },
        { name: "Engadget", url: "https://www.engadget.com" },
        { name: "Ars Technica", url: "https://arstechnica.com" },
        { name: "The Verge", url: "https://www.theverge.com" }
      ];
      
      for (const source of defaultSources) {
        await pool.query(
          'INSERT INTO news_sources (name, url, is_active) VALUES ($1, $2, true)',
          [source.name, source.url]
        );
      }
      console.log('Default news sources inserted');
    }
    
    console.log('Database initialization complete!');
    
  } catch (error) {
    console.error('Error creating tables:', error);
    process.exit(1);
  } finally {
    await pool.end();
  }
}

createTables();