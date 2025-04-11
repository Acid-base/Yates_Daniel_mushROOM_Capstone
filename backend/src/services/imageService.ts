import axios from 'axios';
import Bottleneck from 'bottleneck';
import { Collection, ObjectId } from 'mongodb';
import { uploadBufferToR2 } from './r2Service';

// Create a rate limiter instance based on environment variables
const limiter = new Bottleneck({
  minTime: parseInt(process.env.RATE_LIMIT_MIN_INTERVAL_MS || '5000', 10), // Min time between requests (default 5s)
  maxConcurrent: 1, // Only one request at a time
  reservoir: parseInt(process.env.RATE_LIMIT_REQUESTS_PER_MINUTE || '20', 10), // Max requests per minute
  reservoirRefreshAmount: parseInt(process.env.RATE_LIMIT_REQUESTS_PER_MINUTE || '20', 10),
  reservoirRefreshInterval: 60 * 1000, // 1 minute in milliseconds
});

// Track run times to adjust rate limiting dynamically
let lastRunTime = 0;

/**
 * Fetches an image from mushroomobserver.org with rate limiting
 * @param imageUrl - URL of the image to fetch
 * @returns Buffer containing the image data
 */
export async function fetchImageWithRateLimit(imageUrl: string): Promise<Buffer> {
  // Wait for the longer of 5 seconds or the last run time
  const waitTime = Math.max(5000, lastRunTime);
  console.log(`Waiting ${waitTime}ms before fetching image ${imageUrl}`);

  const startTime = Date.now();

  try {
    // Schedule the request through the rate limiter
    const response = await limiter.schedule(() =>
      axios.get(imageUrl, {
        responseType: 'arraybuffer',
        headers: {
          'User-Agent': 'mushROOM Field Guide/1.0 (educational project)',
          Accept: 'image/jpeg,image/png,image/*',
        },
      })
    );

    // Calculate how long this request took
    const endTime = Date.now();
    lastRunTime = endTime - startTime;

    console.log(`Fetched image ${imageUrl} in ${lastRunTime}ms`);
    return Buffer.from(response.data);
  } catch (error) {
    console.error(`Error fetching image from ${imageUrl}:`, error);
    throw new Error(`Failed to fetch image: ${error instanceof Error ? error.message : String(error)}`);
  }
}

/**
 * Processes a mushroom document to fetch its image and store it in R2
 * @param mushroom - The mushroom document from MongoDB
 * @param mushroomCollection - MongoDB collection to update
 */
export async function processMushroomImage(mushroom: any, mushroomCollection: Collection): Promise<void> {
  // Skip if the mushroom has no image or already has an R2 URL
  if (!mushroom.image?.url || mushroom.image.url.includes(process.env.R2_PUBLIC_URL || '')) {
    return;
  }

  try {
    const imageUrl = mushroom.image.url;
    console.log(`Processing image for ${mushroom.scientific_name} from ${imageUrl}`);

    // Fetch the image with rate limiting
    const imageBuffer = await fetchImageWithRateLimit(imageUrl);

    // Generate a unique filename for R2 storage
    const fileExtension = imageUrl.split('.').pop()?.toLowerCase() || 'jpg';
    const fileName = `mushrooms/${mushroom._id.toString()}-${Date.now()}.${fileExtension}`;

    // Upload to R2 and get the new URL
    const newImageUrl = await uploadBufferToR2(
      imageBuffer,
      fileName,
      `image/${fileExtension === 'png' ? 'png' : 'jpeg'}`
    );

    // Update the mushroom document in MongoDB
    await mushroomCollection.updateOne(
      { _id: new ObjectId(mushroom._id) },
      {
        $set: {
          'image.url': newImageUrl,
          'image.source': 'r2',
          'image.processed_at': new Date(),
          'image.original_url': imageUrl,
        },
      }
    );

    console.log(`Updated image URL for ${mushroom.scientific_name} to ${newImageUrl}`);
  } catch (error) {
    console.error(`Error processing image for ${mushroom.scientific_name}:`, error);
    // Don't throw, just log the error so processing can continue with other mushrooms
  }
}
