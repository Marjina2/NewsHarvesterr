import { Pool } from 'pg';
import { drizzle } from 'drizzle-orm/node-postgres';
import * as schema from "@shared/schema";

// Use DATABASE_URL environment variable for database connection
const databaseUrl = process.env.DATABASE_URL;

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
  console.warn("DATABASE_URL environment variable is not set - using in-memory storage");
}

export { pool, db };