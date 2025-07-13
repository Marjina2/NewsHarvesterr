import { Pool } from '@neondatabase/serverless';
import { drizzle } from 'drizzle-orm/neon-serverless';
import * as schema from "@shared/schema";

// Use SUPABASE_URL environment variable for Supabase connection
const databaseUrl = process.env.SUPABASE_URL;

if (!databaseUrl) {
  throw new Error(
    "SUPABASE_URL environment variable is required. Please set it to your Supabase PostgreSQL connection string.",
  );
}

export const pool = new Pool({ connectionString: databaseUrl });
export const db = drizzle({ client: pool, schema });