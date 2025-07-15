import { Pool } from 'pg';
import { drizzle } from 'drizzle-orm/node-postgres';
import * as schema from "@shared/schema";

// Use DATABASE_URL environment variable for database connection
const databaseUrl = process.env.DATABASE_URL;

let pool: Pool | null = null;
let db: any = null;

if (databaseUrl) {
  try {
    console.log("Connecting to database...");
    
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
    pool = null;
    db = null;
  }
} else {
  console.log("DATABASE_URL not set, using in-memory storage for development");
}

export { pool, db };