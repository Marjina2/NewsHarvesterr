import { Pool } from 'pg';
import { drizzle } from 'drizzle-orm/node-postgres';
import * as schema from "@shared/schema";

// Use SUPABASE_URL environment variable for database connection
const databaseUrl = process.env.SUPABASE_URL;

let pool: Pool | null = null;
let db: any = null;

if (databaseUrl) {
  try {
    pool = new Pool({ 
      connectionString: databaseUrl,
      ssl: databaseUrl.includes('localhost') ? false : { rejectUnauthorized: false }
    });
    db = drizzle({ client: pool, schema });
    console.log("Database connection established successfully");
  } catch (error) {
    console.error("Database connection failed:", error);
    pool = null;
    db = null;
  }
} else {
  console.error("SUPABASE_URL environment variable is not set");
  console.log("Available environment variables:", Object.keys(process.env).filter(key => key.includes('SUPABASE')));
}

export { pool, db };