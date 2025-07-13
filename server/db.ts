import { Pool, neonConfig } from '@neondatabase/serverless';
import { drizzle } from 'drizzle-orm/neon-serverless';
import ws from "ws";
import * as schema from "@shared/schema";

neonConfig.webSocketConstructor = ws;

// Create proper database connection URL for Supabase or Neon
let databaseUrl: string;

if (process.env.SUPABASE_URL) {
  // Extract the connection string for Supabase
  const supabaseUrl = process.env.SUPABASE_URL;
  const projectRef = supabaseUrl.split('//')[1].split('.')[0];
  databaseUrl = `postgresql://postgres.${projectRef}:[YOUR-PASSWORD]@aws-0-us-west-1.pooler.supabase.com:6543/postgres`;
  
  // For now, use the Neon database while we configure Supabase properly
  if (!process.env.DATABASE_URL) {
    throw new Error("Please use DATABASE_URL for now while we configure Supabase properly");
  }
  databaseUrl = process.env.DATABASE_URL;
} else if (process.env.DATABASE_URL) {
  databaseUrl = process.env.DATABASE_URL;
} else {
  throw new Error(
    "DATABASE_URL must be set. Did you forget to provision a database?",
  );
}

export const pool = new Pool({ connectionString: databaseUrl });
export const db = drizzle({ client: pool, schema });