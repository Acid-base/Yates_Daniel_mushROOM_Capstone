/**
 * mushROOM Image Processor Worker
 *
 * This Cloudflare Worker handles:
 * 1. Rate-limited image retrieval from mushroomobserver.org
 * 2. Uploading images to Cloudflare R2 storage
 * 3. Updating MongoDB records with new image URLs
 */

import { connect } from './db';
import dotenv from 'dotenv';
dotenv.config();
import { ScheduledEvent, ExecutionContext } from '@cloudflare/workers-types';

// Types for our environment bindings
interface Env {
  // R2 Bucket binding (corrected type)
  MUSHROOM_IMAGES: R2Bucket;

  // Environment variables
  MONGODB_CONNECTION_STRING: string;
  DB_NAME: string;
  COLLECTION_NAME: string;
  RATE_LIMIT_REQUESTS_PER_MINUTE: string;
  RATE_LIMIT_MIN_INTERVAL_MS: string;
  
  // Optional API token if needed
  API_TOKEN?: string;
}

// CRON triggered handler
export default {
  // This is the main entry point for scheduled execution
  async scheduled(event: ScheduledEvent, env: Env, ctx: ExecutionContext): Promise<void> {
    console.log("Starting scheduled mushroom image processing job");
    
    try {
      await processMushroomImages(env);
      console.log("Scheduled image processing completed successfully");
    } catch (error) {
      console.error("Error during scheduled image processing:", error);
    }
  },

  // Fetch handler for manual triggering or checking status
  async fetch(request: Request, env: Env, ctx: ExecutionContext): Promise<Response> {
    const url = new URL(request.url);
    
    // Simple status endpoint
    if (url.pathname === "/status") {
      return new Response(JSON.stringify({
        status: "ok",
        worker: "mushroom-image-processor",
        timestamp: new Date().toISOString()
      }), {
        headers: {
          "Content-Type": "application/json"
        }
      });
    }
    
    // Manual trigger endpoint (protected with a simple auth check)
    if (url.pathname === "/process" && request.method === "POST") {
      // In production, add proper authentication here
      
      // Process in the background so the request can return quickly
      ctx.waitUntil(processMushroomImages(env));
      
      return new Response(JSON.stringify({
        status: "processing",
        message: "Image processing job started in the background",
        timestamp: new Date().toISOString()
      }), {
        headers: {
          "Content-Type": "application/json"
        }
      });
    }
    
    // Default response for other paths
    return new Response("Not found", { status: 404 });
  }
};

/**
 * Main function to process mushroom images from MongoDB to R2
 */
async function processMushroomImages(env: Env): Promise<void> {
  // Connect to MongoDB
  const { client, db } = await connect(env.MONGODB_CONNECTION_STRING);
  const collection = db.collection(env.COLLECTION_NAME);
  
  try {
    // Track state
    const batchSize = 5;
    let lastProcessedTimestamp = 0;
    let processedCount = 0;
    let hasMoreImages = true;
    
    // Process in batches
    while (hasMoreImages) {
      // Find mushrooms with unprocessed images (corrected query)
      const mushrooms = await collection.find({
        'image.url': { $exists: true, $ne: null }, // Combined conditions
        $or: [
          { 'image.source': { $ne: 'r2' } },
          { 'image.source': { $exists: false } }
        ]
      }).limit(batchSize).toArray();
      
      // Exit loop if no more mushrooms to process
      if (mushrooms.length === 0) {
        hasMoreImages = false;
        break;
      }
      
      console.log(`Processing batch of ${mushrooms.length} mushrooms`);
      
      // Process each mushroom sequentially with rate limiting
      for (const mushroom of mushrooms) {
        // Apply rate limiting
        const currentTime = Date.now();
        const minInterval = parseInt(env.RATE_LIMIT_MIN_INTERVAL_MS, 10) || 5000;
        const waitTime = Math.max(0, minInterval - (currentTime - lastProcessedTimestamp));
        
        if (waitTime > 0) {
          console.log(`Rate limiting: waiting ${waitTime}ms before next request`);
          await new Promise(resolve => setTimeout(resolve, waitTime));
        }
        
        try {
          // Process this mushroom's image
          await processMushroomImage(mushroom, collection, env);
          processedCount++;
          lastProcessedTimestamp = Date.now();
        } catch (error) {
          console.error(`Error processing image for mushroom ${mushroom._id}:`, error);
          // Continue with next mushroom
        }
      }
      
      // Small delay between batches
      await new Promise(resolve => setTimeout(resolve, 1000));
    }
    
    console.log(`Image processing completed. Total processed: ${processedCount}`);
  } finally {
    // Close MongoDB connection
    await client.close();
  }
}

/**
 * Process a single mushroom's image
 */
async function processMushroomImage(mushroom: any, collection: any, env: Env): Promise<void> {
  const imageUrl = mushroom.image?.url;
  
  // Skip if no image or already processed
  if (!imageUrl || imageUrl.includes('r2.dev') || imageUrl.includes('cloudflare')) {
    return;
  }
  
  console.log(`Processing image for ${mushroom.scientific_name} from ${imageUrl}`);
  
  // Start timer to track request time
  const startTime = Date.now();
  
  try {
    // Fetch the image with additional headers
    const response = await fetch(imageUrl, {
      headers: {
        'User-Agent': 'mushROOM Field Guide/1.0 (educational project)',
        'Accept': 'image/jpeg,image/png,image/*'
      }
    });
    
    if (!response.ok) {
      throw new Error(`Failed to fetch image: ${response.status} ${response.statusText}`);
    }
    
    // Get image data as array buffer
    const imageData = await response.arrayBuffer();
    
    // Generate a unique filename
    const fileExtension = imageUrl.split('.').pop()?.toLowerCase() || 'jpg';
    const fileName = `mushrooms/${mushroom._id}-${Date.now()}.${fileExtension}`;
    
    // Upload to R2
    await env.MUSHROOM_IMAGES.put(fileName, imageData, {
      httpMetadata: {
        contentType: `image/${fileExtension === 'png' ? 'png' : 'jpeg'}`
      }
    });
    
    // Get the R2 public URL (corrected to use S3-compatible format)
    // Using Cloudflare R2 public bucket endpoint format
    const r2PublicUrl = `https://${env.MUSHROOM_IMAGES.name}.${env.R2_ACCOUNT_ID}.r2.cloudflarestorage.com/${fileName}`;
    
    // Update MongoDB
    await collection.updateOne(
      { _id: mushroom._id },
      {
        $set: {
          'image.url': r2PublicUrl,
          'image.source': 'r2',
          'image.processed_at': new Date(),
          'image.original_url': imageUrl
        }
      }
    );
    
    // Calculate request time for rate limiting
    const requestTime = Date.now() - startTime;
    console.log(`Processed image for ${mushroom.scientific_name} in ${requestTime}ms`);
    
  } catch (error) {
    console.error(`Error processing image for ${mushroom.scientific_name}:`, error);
    throw error;
  }
}
