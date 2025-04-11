import { GetObjectCommand, PutObjectCommand, S3Client } from '@aws-sdk/client-s3';
import { getSignedUrl } from '@aws-sdk/s3-request-presigner';

// Initialize the S3 client with Cloudflare R2 credentials using jurisdiction-specific endpoint
const s3Client = new S3Client({
  region: 'auto',
  endpoint: process.env.R2_ENDPOINT || 'https://c567e4f3c8382ad51dcee625313aef85.r2.cloudflarestorage.com',
  credentials: {
    accessKeyId: process.env.R2_ACCESS_KEY_ID || '',
    secretAccessKey: process.env.R2_SECRET_ACCESS_KEY || '',
  },
});

const bucketName = process.env.R2_BUCKET_NAME || 'mushroom-images';
const publicUrl = process.env.R2_PUBLIC_URL || '';

/**
 * Uploads a buffer to Cloudflare R2 storage
 *
 * @param buffer - Image buffer to upload
 * @param key - The key (path) in the bucket
 * @param contentType - Content type of the image
 * @returns The URL of the uploaded image
 */
export async function uploadBufferToR2(
  buffer: Buffer,
  key: string,
  contentType: string = 'image/jpeg'
): Promise<string> {
  try {
    const command = new PutObjectCommand({
      Bucket: bucketName,
      Key: key,
      Body: buffer,
      ContentType: contentType,
    });

    await s3Client.send(command);

    // Return the public URL of the uploaded image
    return `${publicUrl}/${key}`;
  } catch (error) {
    console.error('Error uploading image to R2:', error);
    throw new Error(`Failed to upload image to R2: ${error instanceof Error ? error.message : String(error)}`);
  }
}

/**
 * Generates a signed URL for retrieving an object from R2
 *
 * @param key - The key (path) in the bucket
 * @param expiresIn - Seconds until the signed URL expires (default: 3600)
 * @returns Signed URL for accessing the object
 */
export async function getSignedR2Url(key: string, expiresIn: number = 3600): Promise<string> {
  const command = new GetObjectCommand({
    Bucket: bucketName,
    Key: key,
  });

  return await getSignedUrl(s3Client, command, { expiresIn });
}
