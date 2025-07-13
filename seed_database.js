import { Pool } from '@neondatabase/serverless';
import { drizzle } from 'drizzle-orm/neon-serverless';
import { newsSources } from './shared/schema.ts';

// Use SUPABASE_URL for Supabase connection
const databaseUrl = process.env.SUPABASE_URL;

const pool = new Pool({ connectionString: databaseUrl });
const db = drizzle(pool);

const defaultSources = [
  // International News
  { name: "BBC News", url: "https://www.bbc.com/news", isActive: true },
  { name: "CNN", url: "https://edition.cnn.com", isActive: true },
  { name: "The Guardian", url: "https://www.theguardian.com/international", isActive: true },
  { name: "NPR News", url: "https://www.npr.org/sections/news", isActive: true },
  { name: "Associated Press", url: "https://apnews.com", isActive: true },
  
  // Technology News
  { name: "TechCrunch", url: "https://techcrunch.com", isActive: true },
  { name: "The Verge", url: "https://www.theverge.com", isActive: true },
  { name: "Engadget", url: "https://www.engadget.com", isActive: true },
  { name: "Ars Technica", url: "https://arstechnica.com", isActive: true },
  { name: "WIRED", url: "https://www.wired.com", isActive: true },
  { name: "Hacker News", url: "https://news.ycombinator.com", isActive: true },
  
  // Indian News Sources
  { name: "India Today", url: "https://www.indiatoday.in", isActive: true },
  { name: "NDTV", url: "https://www.ndtv.com", isActive: true },
  { name: "Times of India", url: "https://timesofindia.indiatimes.com", isActive: true },
  { name: "The Hindu", url: "https://www.thehindu.com", isActive: true },
  { name: "Economic Times", url: "https://economictimes.indiatimes.com", isActive: true },
  
  // Business & Finance
  { name: "Bloomberg", url: "https://www.bloomberg.com", isActive: true },
  { name: "Wall Street Journal", url: "https://www.wsj.com", isActive: true },
  { name: "Forbes", url: "https://www.forbes.com", isActive: true },
  { name: "Financial Times", url: "https://www.ft.com", isActive: true }
];

async function seedDatabase() {
  console.log('Seeding database with default news sources...');
  
  try {
    // Insert default sources
    await db.insert(newsSources).values(defaultSources);
    console.log(`Successfully added ${defaultSources.length} news sources`);
    
    // Show the sources
    const sources = await db.select().from(newsSources);
    console.log('Current sources in database:');
    sources.forEach(source => {
      console.log(`- ${source.name} (${source.url})`);
    });
    
  } catch (error) {
    console.error('Error seeding database:', error);
  }
  
  await pool.end();
}

seedDatabase();