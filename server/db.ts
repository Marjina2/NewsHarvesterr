import { Pool } from 'pg';
import { drizzle } from 'drizzle-orm/node-postgres';
import * as schema from "@shared/schema";

// Use SUPABASE_URL environment variable for database connection
const databaseUrl = process.env.SUPABASE_URL;

let pool: Pool | null = null;
let db: any = null;

if (databaseUrl) {
  try {
    console.log("Connecting to database with URL:", databaseUrl.substring(0, 50) + "...");
    console.log("Database URL contains password:", databaseUrl.includes(':') && databaseUrl.split(':').length > 3);

    pool = new Pool({ 
      connectionString: databaseUrl,
      ssl: databaseUrl.includes('localhost') ? false : { rejectUnauthorized: false },
      // Add connection timeout and retry settings
      connectionTimeoutMillis: 10000,
      query_timeout: 5000,
      max: 5
    });

    db = drizzle({ client: pool, schema });

    // Test the connection
    await pool.query('SELECT 1');
    console.log("Database connection established successfully");
  } catch (error) {
    console.error("Database connection failed:", error.message);
    console.error("Full error:", error);
    pool = null;
    db = null;
  }
} else {
  console.error("SUPABASE_URL environment variable is not set");
  console.log("Available environment variables:", Object.keys(process.env).filter(key => key.includes('SUPABASE')));
}

export { pool, db };