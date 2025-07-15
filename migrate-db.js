import { Pool } from 'pg';

const databaseUrl = process.env.DATABASE_URL;

if (!databaseUrl) {
  console.error("DATABASE_URL environment variable is not set");
  process.exit(1);
}

const pool = new Pool({ 
  connectionString: databaseUrl,
  ssl: databaseUrl.includes('localhost') ? false : { rejectUnauthorized: false }
});

async function createTables() {
  try {
    console.log("Creating database tables...");

    // Create news_sources table
    await pool.query(`
      CREATE TABLE IF NOT EXISTS news_sources (
        id SERIAL PRIMARY KEY,
        name TEXT NOT NULL,
        url TEXT NOT NULL,
        is_active BOOLEAN DEFAULT true,
        created_at TIMESTAMP DEFAULT NOW(),
        updated_at TIMESTAMP DEFAULT NOW()
      );
    `);

    // Create news_articles table
    await pool.query(`
      CREATE TABLE IF NOT EXISTS news_articles (
        id SERIAL PRIMARY KEY,
        title TEXT NOT NULL,
        url TEXT NOT NULL,
        content TEXT,
        image_url TEXT,
        source_url TEXT NOT NULL,
        category TEXT DEFAULT 'general',
        region TEXT DEFAULT 'international',
        status TEXT DEFAULT 'pending',
        rephrased_title TEXT,
        created_at TIMESTAMP DEFAULT NOW(),
        updated_at TIMESTAMP DEFAULT NOW(),
        scraped_at TIMESTAMP DEFAULT NOW(),
        rephrased_at TIMESTAMP
      );
    `);

    // Create scraper_config table
    await pool.query(`
      CREATE TABLE IF NOT EXISTS scraper_config (
        id SERIAL PRIMARY KEY,
        is_active BOOLEAN DEFAULT false,
        interval_minutes INTEGER DEFAULT 30,
        last_run_at TIMESTAMP,
        created_at TIMESTAMP DEFAULT NOW(),
        updated_at TIMESTAMP DEFAULT NOW()
      );
    `);

    console.log("✓ Tables created successfully!");

    // Insert default sources
    const existingSources = await pool.query('SELECT COUNT(*) FROM news_sources');
    if (parseInt(existingSources.rows[0].count) === 0) {
      console.log("Adding default news sources...");
      
      const defaultSources = [
        { name: "BBC News", url: "https://www.bbc.com/news", is_active: true },
        { name: "Reuters", url: "https://www.reuters.com", is_active: true },
        { name: "TechCrunch", url: "https://techcrunch.com", is_active: true },
        { name: "Hacker News", url: "https://news.ycombinator.com", is_active: true },
        { name: "CNN", url: "https://www.cnn.com", is_active: true },
        { name: "The Guardian", url: "https://www.theguardian.com", is_active: true },
        { name: "NPR", url: "https://www.npr.org", is_active: true },
        { name: "Associated Press", url: "https://apnews.com", is_active: true },
        { name: "India Today", url: "https://www.indiatoday.in", is_active: true },
        { name: "NDTV", url: "https://www.ndtv.com", is_active: true },
        { name: "Times of India", url: "https://timesofindia.indiatimes.com", is_active: true },
        { name: "The Hindu", url: "https://www.thehindu.com", is_active: true },
        { name: "Economic Times", url: "https://economictimes.indiatimes.com", is_active: true },
        { name: "WIRED", url: "https://www.wired.com", is_active: true },
        { name: "Engadget", url: "https://www.engadget.com", is_active: true },
        { name: "Ars Technica", url: "https://arstechnica.com", is_active: true },
        { name: "The Verge", url: "https://www.theverge.com", is_active: true },
      ];

      for (const source of defaultSources) {
        await pool.query(
          'INSERT INTO news_sources (name, url, is_active) VALUES ($1, $2, $3)',
          [source.name, source.url, source.is_active]
        );
      }
      
      console.log("✓ Default sources added!");
    }

    // Insert default scraper config
    const existingConfig = await pool.query('SELECT COUNT(*) FROM scraper_config');
    if (parseInt(existingConfig.rows[0].count) === 0) {
      console.log("Adding default scraper configuration...");
      await pool.query(
        'INSERT INTO scraper_config (is_active, interval_minutes) VALUES ($1, $2)',
        [false, 30]
      );
      console.log("✓ Default config added!");
    }

    console.log("🎉 Database migration completed successfully!");
    
  } catch (error) {
    console.error("Migration failed:", error);
    process.exit(1);
  } finally {
    await pool.end();
  }
}

createTables();