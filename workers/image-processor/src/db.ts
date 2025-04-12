/**
 * MongoDB connection module for the Cloudflare Worker
 */
import { MongoClient } from 'mongodb';

// Cache the client connection to reuse across requests
let cachedClient: MongoClient | null = null;

/**
 * Connects to MongoDB and returns the client and database
 */
export async function connect(connectionString: string) {
  if (!connectionString) {
    throw new Error('Missing MongoDB connection string');
  }

  // Use cached client if available
  if (cachedClient) {
    return {
      client: cachedClient,
      db: cachedClient.db(process.env.DB_NAME || 'mushroom_field_guide')
    };
  }

  // Create a new client
  const client = new MongoClient(connectionString);
  await client.connect();
  console.log('Connected to MongoDB successfully');

  // Cache for future use
  cachedClient = client;

  return {
    client,
    db: client.db(process.env.DB_NAME || 'mushroom_field_guide')
  };
}
