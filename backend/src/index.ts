// src/index.ts

// --- Imports ---
import cors from 'cors';
import dotenv from 'dotenv';
import express, { Request, Response, Express } from 'express';
import { Collection, Db, MongoClient, ObjectId, FindOptions, Timestamp, UpdateFilter } from 'mongodb'; // Added FindOptions, Timestamp, UpdateFilter
import path from 'path';
import axios from 'axios'; // Now correctly recognized after installation
import Bottleneck from 'bottleneck'; // Now correctly recognized after installation
import { GetObjectCommand, PutObjectCommand, S3Client } from '@aws-sdk/client-s3'; // Now correctly recognized
import { getSignedUrl } from '@aws-sdk/s3-request-presigner'; // Now correctly recognized
import { Buffer } from 'buffer';

// --- Configuration Loading & Validation ---

function loadConfig() {
    // Load from .env file relative to this script's potential build location (e.g., dist/)
    // Adjust the path if your build structure is different or if running directly with ts-node from src/
    dotenv.config({ path: path.resolve(__dirname, '../../.env') });

    const config = {
        mongoUri: process.env.MONGODB_CONNECTION_STRING,
        dbName: process.env.DB_NAME,
        collectionName: process.env.COLLECTION_NAME,
        port: process.env.PORT || '5000',
        r2Endpoint: process.env.R2_ENDPOINT,
        r2AccessKeyId: process.env.R2_ACCESS_KEY_ID,
        r2SecretAccessKey: process.env.R2_SECRET_ACCESS_KEY,
        r2BucketName: process.env.R2_BUCKET_NAME || 'mushroom-images',
        r2PublicUrl: process.env.R2_PUBLIC_URL,
        rateLimitMinIntervalMs: parseInt(process.env.RATE_LIMIT_MIN_INTERVAL_MS || '5000', 10),
        rateLimitRequestsPerMinute: parseInt(process.env.RATE_LIMIT_REQUESTS_PER_MINUTE || '20', 10),
        allowedOrigins: ['http://127.0.0.1:5173', 'http://localhost:5173'],
        atlasSearchIndex: 'mushroom_search',
    };

    if (!config.mongoUri || !config.dbName || !config.collectionName) {
        console.error('Error: Missing critical MongoDB connection details in .env');
        process.exit(1);
    }
    if (!config.r2Endpoint || !config.r2AccessKeyId || !config.r2SecretAccessKey || !config.r2BucketName || !config.r2PublicUrl) {
        console.warn('Warning: Missing R2 configuration details in .env. Image processing/uploading might fail.');
    }

    return config;
}

const config = loadConfig();

// --- Interfaces ---
interface NameParams { name: string; }
interface FieldParams { field: string; }
interface CountRequestBody { filter?: any; }
interface FindRequestBody { filter?: any; limit?: number; skip?: number; sort?: any; }
interface SearchRequestBody { query: string; limit?: number; skip?: number; }
interface IdParams { id: string; }

// Define a more specific Mushroom Document type based on your actual schema
interface MushroomDocument {
    _id: ObjectId;
    scientific_name: string;
    common_name?: string;
    image?: {
        url?: string;
        source?: string;
        processed_at?: Date;
        original_url?: string;
        processing_error?: string; // To store error messages
        processing_failed_at?: Date; // To track when an error occurred
    };
    classification?: {
        family?: string;
        // other classification fields
    };
    description?: {
        habitat?: string;
        uses?: string;
        // other description fields
    };
    regional_distribution?: {
        countries?: string[];
        states?: string[];
        regions?: string[];
        // other distribution fields
    };
    // Add any other top-level fields from your schema
}


// --- Service Initializations ---

function initializeS3Client(cfg: typeof config): S3Client {
    if (!cfg.r2Endpoint || !cfg.r2AccessKeyId || !cfg.r2SecretAccessKey) {
        console.warn("Cannot initialize S3 client due to missing R2 credentials/endpoint. Uploads will fail.");
        // Return a minimal client instance; operations requiring credentials will fail.
        return new S3Client({ region: 'auto', endpoint: cfg.r2Endpoint });
    }
    return new S3Client({
        region: 'auto',
        endpoint: cfg.r2Endpoint,
        credentials: {
            accessKeyId: cfg.r2AccessKeyId,
            secretAccessKey: cfg.r2SecretAccessKey,
        },
    });
}

function initializeRateLimiter(cfg: typeof config): Bottleneck {
    return new Bottleneck({
        minTime: cfg.rateLimitMinIntervalMs,
        maxConcurrent: 1,
        reservoir: cfg.rateLimitRequestsPerMinute,
        reservoirRefreshAmount: cfg.rateLimitRequestsPerMinute,
        reservoirRefreshInterval: 60 * 1000,
    });
}

const s3Client = initializeS3Client(config);
const limiter = initializeRateLimiter(config);
let lastImageFetchRunTime = 0; // State for rate limiting


// --- Helper Functions ---

function buildMongoQueryFilter(filter: any = {}): any {
    const queryFilter: any = {};
    if (filter?.scientific_name) queryFilter.scientific_name = { $regex: filter.scientific_name, $options: 'i' };
    if (filter?.common_name) queryFilter.common_name = { $regex: filter.common_name, $options: 'i' };
    if (filter?.family) queryFilter['classification.family'] = { $regex: filter.family, $options: 'i' };
    if (filter?.habitat) queryFilter['description.habitat'] = { $regex: filter.habitat, $options: 'i' };
    if (filter?.country) queryFilter['regional_distribution.countries'] = filter.country;
    if (filter?.state) queryFilter['regional_distribution.states'] = filter.state;
    if (filter?.region) queryFilter['regional_distribution.regions'] = filter.region;
    if (filter?.uses) queryFilter['description.uses'] = { $regex: filter.uses, $options: 'i' };
    return queryFilter;
}

async function uploadBufferToR2(
    client: S3Client,
    bucket: string,
    publicBaseUrl: string,
    buffer: Buffer,
    key: string,
    contentType: string = 'image/jpeg'
): Promise<string> {
    if (!publicBaseUrl || !key || !bucket) {
        throw new Error('R2 configuration (bucket, public URL) or upload key is missing.');
    }
    try {
        const command = new PutObjectCommand({ Bucket: bucket, Key: key, Body: buffer, ContentType: contentType });
        await client.send(command);
        return `${publicBaseUrl}/${key}`;
    } catch (error) {
        console.error('Error uploading image to R2:', error);
        throw new Error(`Failed to upload image to R2: ${error instanceof Error ? error.message : String(error)}`);
    }
}

async function getSignedR2Url(
    client: S3Client,
    bucket: string,
    key: string,
    expiresIn: number = 3600
): Promise<string> {
    const command = new GetObjectCommand({ Bucket: bucket, Key: key });
    return getSignedUrl(client, command, { expiresIn });
}

async function fetchImageWithRateLimit(
    rateLimiter: Bottleneck,
    imageUrl: string
): Promise<Buffer> {
    const waitTime = Math.max(config.rateLimitMinIntervalMs, lastImageFetchRunTime);
    console.log(`Waiting ${waitTime}ms before fetching image ${imageUrl}`);
    const startTime = Date.now();
    try {
        const response = await rateLimiter.schedule(() =>
            axios.get(imageUrl, {
                responseType: 'arraybuffer',
                headers: { 'User-Agent': 'mushROOM Field Guide/1.0 (educational project)', 'Accept': 'image/jpeg,image/png,image/*' },
            })
        );
        const endTime = Date.now();
        lastImageFetchRunTime = endTime - startTime;
        console.log(`Fetched image ${imageUrl} in ${lastImageFetchRunTime}ms`);
        return Buffer.from(response.data);
    } catch (error) {
        const endTime = Date.now();
        lastImageFetchRunTime = endTime - startTime;
        console.error(`Error fetching image from ${imageUrl} (took ${lastImageFetchRunTime}ms):`, error);
        throw new Error(`Failed to fetch image: ${error instanceof Error ? error.message : String(error)}`);
    }
}

async function processSingleMushroomImage(
    mushroom: MushroomDocument,
    collection: Collection<MushroomDocument>,
    r2Client: S3Client,
    rateLimiter: Bottleneck,
    appConfig: typeof config
): Promise<void> {
    if (!mushroom?._id) { console.warn("Skipping: Invalid mushroom object."); return; }
    if (!appConfig.r2PublicUrl || !appConfig.r2BucketName) { console.warn(`Skipping ${mushroom.scientific_name}: R2 config incomplete.`); return; }
    const imageUrl = mushroom.image?.url;
    if (!imageUrl || typeof imageUrl !== 'string') { console.log(`Skipping ${mushroom.scientific_name}: No valid image URL.`); return; }
    if (imageUrl.includes(appConfig.r2PublicUrl)) { console.log(`Skipping ${mushroom.scientific_name}: Image already in R2.`); return; }

    console.log(`Processing image for ${mushroom.scientific_name} (${mushroom._id}) from ${imageUrl}`);
    try {
        const imageBuffer = await fetchImageWithRateLimit(rateLimiter, imageUrl);
        const urlParts = imageUrl.split('.');
        const fileExtension = urlParts.length > 1 ? urlParts.pop()?.toLowerCase() || 'jpg' : 'jpg';
        const validExtension = ['jpg', 'jpeg', 'png', 'gif', 'webp'].includes(fileExtension) ? fileExtension : 'jpg';
        const fileName = `mushrooms/${mushroom._id.toString()}-${Date.now()}.${validExtension}`;
        const contentType = `image/${validExtension === 'jpg' ? 'jpeg' : validExtension}`;

        const newImageUrl = await uploadBufferToR2(
            r2Client, appConfig.r2BucketName, appConfig.r2PublicUrl, imageBuffer, fileName, contentType
        );

        // --- CORRECTED PAYLOAD ---
        const updatePayload: UpdateFilter<MushroomDocument> = { // Explicitly use UpdateFilter type
            $set: {
                'image.url': newImageUrl,
                'image.source': 'r2',
                'image.processed_at': new Date(),
                'image.original_url': imageUrl,
            },
            $unset: {
                'image.processing_error': "", // Correct value for $unset
                'image.processing_failed_at': "" // Correct value for $unset
            }
        };
        // --- END CORRECTION ---

        await collection.updateOne({ _id: mushroom._id }, updatePayload);
        console.log(`Successfully updated image URL for ${mushroom.scientific_name} (${mushroom._id}) to ${newImageUrl}`);

    } catch (error) {
        const errorMessage = error instanceof Error ? error.message : String(error);
        console.error(`Error processing image for ${mushroom.scientific_name} (${mushroom._id}):`, errorMessage);
        try {
            const errorUpdatePayload: UpdateFilter<MushroomDocument> = { // Explicitly use UpdateFilter type
                $set: {
                    'image.processing_error': errorMessage,
                    'image.processing_failed_at': new Date(),
                }
            };
            await collection.updateOne({ _id: mushroom._id }, errorUpdatePayload);
        } catch (updateError) {
            console.error(`Failed to log image processing error for ${mushroom.scientific_name} (${mushroom._id}):`, updateError);
        }
    }
}


// --- Database Connection ---

async function connectToDatabase(uri: string, dbName: string, collectionName: string): Promise<{ db: Db; collection: Collection<MushroomDocument> }> {
    try {
        const client = await MongoClient.connect(uri);
        console.log('Connected successfully to MongoDB');
        const db = client.db(dbName);
        const collection = db.collection<MushroomDocument>(collectionName);
        // Optional: Add index creation here if needed
        // await collection.createIndex({ scientific_name: 1 });
        // await collection.createIndex({ "regional_distribution.countries": 1 });
        // etc.
        return { db, collection };
    } catch (err) {
        console.error('Failed to connect to MongoDB', err);
        throw err;
    }
}


// --- Express Application Setup ---

function createApp(appConfig: typeof config): Express {
    const app = express();
    app.use(cors({
        origin: appConfig.allowedOrigins,
        methods: ['GET', 'POST', 'PUT', 'DELETE', 'OPTIONS'],
        allowedHeaders: ['Content-Type', 'Authorization'],
        credentials: true,
    }));
    app.use(express.json());
    return app;
}


// --- Route Handlers (Defined as separate functions) ---

async function handleHealthCheck(req: Request, res: Response, dbInstance: Db | null) {
    res.status(200).json({ status: 'OK', message: 'Server is running', dbConnected: !!dbInstance });
}

async function handleFindMushrooms(req: Request<{}, {}, FindRequestBody>, res: Response, collection: Collection<MushroomDocument>) {
    try {
        const { filter = {}, limit = 10, skip = 0, sort } = req.body;
        const queryFilter = buildMongoQueryFilter(filter);
        const options: FindOptions<MushroomDocument> = { skip, limit }; // Use specific FindOptions type
        if (sort) { options.sort = sort; }

        const documents = await collection.find(queryFilter, options).toArray();
        const totalCount = await collection.countDocuments(queryFilter);

        res.json({ data: documents || [], pagination: { skip, limit, total: totalCount } });
    } catch (error) {
        console.error('Error fetching mushrooms:', error);
        const message = error instanceof Error ? error.message : 'An unknown error occurred';
        res.status(500).json({ error: 'Failed to fetch mushrooms', message });
    }
}

async function handleGetMushroomById(req: Request<IdParams>, res: Response, collection: Collection<MushroomDocument>) {
    try {
        const { id } = req.params;
        if (!ObjectId.isValid(id)) { return res.status(400).json({ error: 'Invalid ID format' }); }
        const document = await collection.findOne({ _id: new ObjectId(id) });
        if (!document) { return res.status(404).json({ error: 'Mushroom not found' }); }
        res.json(document);
    } catch (error) {
        console.error(`Error fetching mushroom by ID ${req.params.id}:`, error);
        const message = error instanceof Error ? error.message : 'An unknown error occurred';
        res.status(500).json({ error: 'Failed to fetch mushroom', message });
    }
}

async function handleGetMushroomBySciName(req: Request<NameParams>, res: Response, collection: Collection<MushroomDocument>) {
    try {
        const decodedName = decodeURIComponent(req.params.name);
        const document = await collection.findOne({ scientific_name: { $regex: `^${decodedName}$`, $options: 'i' } });
        if (!document) { return res.status(404).json({ error: 'Mushroom not found by scientific name' }); }
        res.json(document);
    } catch (error) {
        console.error(`Error fetching mushroom by scientific name ${req.params.name}:`, error);
        const message = error instanceof Error ? error.message : 'An unknown error occurred';
        res.status(500).json({ error: 'Failed to fetch mushroom by scientific name', message });
    }
}

async function handleGetDistinctField(req: Request<FieldParams>, res: Response, collection: Collection<MushroomDocument>) {
    try {
        const decodedField = decodeURIComponent(req.params.field);
        const allowedFields = [
            'scientific_name', 'common_name', 'classification.family', 'description.habitat',
            'regional_distribution.countries', 'regional_distribution.states',
            'regional_distribution.regions', 'description.uses',
        ];
        if (!allowedFields.includes(decodedField)) {
            return res.status(400).json({ error: 'Invalid field for distinct query', message: `Field must be one of: ${allowedFields.join(', ')}` });
        }
        // Assert the type for the distinct method key to satisfy TypeScript
        const values = await collection.distinct(decodedField as keyof MushroomDocument);
        res.json(values || []);
    } catch (error) {
        console.error(`Error fetching distinct values for field ${req.params.field}:`, error);
        const message = error instanceof Error ? error.message : 'An unknown error occurred';
        res.status(500).json({ error: 'Failed to fetch distinct values', message });
    }
}

async function handleSearchMushrooms(req: Request<{}, {}, SearchRequestBody>, res: Response, collection: Collection<MushroomDocument>, appConfig: typeof config) {
    try {
        const { query, limit = 10, skip = 0 } = req.body;
        if (!query || typeof query !== 'string' || query.trim() === '') {
            return res.status(400).json({ error: 'Search query is required and must be a non-empty string' });
        }

        const searchPipelineBase = [{ $search: { index: appConfig.atlasSearchIndex, text: { query: query, path: { wildcard: '*' } } } }];
        const resultsPipeline = [ ...searchPipelineBase, { $addFields: { searchScore: { $meta: 'searchScore' } } }, { $sort: { searchScore: -1 } }, { $skip: skip }, { $limit: limit }];
        const countPipeline = [...searchPipelineBase, { $count: 'total' }];

        const [searchResults, countResult] = await Promise.all([
            collection.aggregate(resultsPipeline).toArray(),
            collection.aggregate(countPipeline).toArray()
        ]);
        const totalCount = countResult.length > 0 ? countResult[0].total : 0;

        res.json({ data: searchResults || [], pagination: { skip, limit, total: totalCount } });
    } catch (error) {
        console.error('Error performing Atlas Search:', error);
        const message = error instanceof Error ? error.message : 'An unknown error occurred';
        if (message.includes('$search') || message.includes('search index')) {
            console.error(`Atlas Search Error: Index '${appConfig.atlasSearchIndex}' might be missing or misconfigured.`);
            return res.status(500).json({ error: 'Search service unavailable', message: 'Search index error.' });
        }
        res.status(500).json({ error: 'Failed to perform search', message });
    }
}

async function handleCountMushrooms(req: Request<{}, {}, CountRequestBody>, res: Response, collection: Collection<MushroomDocument>) {
    try {
        const { filter = {} } = req.body;
        const queryFilter = buildMongoQueryFilter(filter);
        const count = await collection.countDocuments(queryFilter);
        res.json({ count });
    } catch (error) {
        console.error('Error counting mushrooms:', error);
        const message = error instanceof Error ? error.message : 'An unknown error occurred';
        res.status(500).json({ error: 'Failed to count mushrooms', message });
    }
}

// WARNING: Secure this endpoint with authentication/authorization in a real application!
async function handleProcessImages(req: Request, res: Response, collection: Collection<MushroomDocument>, r2Client: S3Client, rateLimiter: Bottleneck, appConfig: typeof config) {
    if (!appConfig.r2PublicUrl || !appConfig.r2BucketName || !r2Client) {
        return res.status(500).json({ error: 'R2 configuration incomplete or client not initialized.' });
    }
    console.log("Starting image processing job...");
    let processedCount = 0;
    let errorCount = 0;
    const batchLimit = 50;

    try {
        const query = {
            'image.url': { $exists: true, $ne: null, $not: new RegExp(appConfig.r2PublicUrl.replace(/[.*+?^${}()|[\]\\]/g, '\\$&')) },
            'image.source': { $ne: 'r2' },
            // Optional: filter out recently failed
            // 'image.processing_failed_at': { $not: { $gt: new Date(Date.now() - 24 * 60 * 60 * 1000) } }
        };
        const mushroomsToProcessCursor = collection.find(query).limit(batchLimit);

        for await (const mushroom of mushroomsToProcessCursor) {
            try {
                // Pass dependencies explicitly
                await processSingleMushroomImage(mushroom, collection, r2Client, rateLimiter, appConfig);
                processedCount++;
            } catch (imageError) { // Catching errors *from* processSingleMushroomImage isn't strictly necessary here as it handles its own logging/DB updates
                errorCount++; // Increment error count if the wrapper loop catches something unexpected
                console.error(`Unexpected error in image processing loop for ${mushroom._id}:`, imageError)
            }
        }
        console.log(`Image processing job finished. Processed: ${processedCount}, Errors: ${errorCount}`);
        res.status(200).json({ message: 'Image processing job finished.', processed: processedCount, errors: errorCount });

    } catch (error) {
        console.error('Error triggering batch image processing:', error);
        res.status(500).json({ error: 'Failed to run image processing job', message: error instanceof Error ? error.message : String(error) });
    }
}


// --- Route Definition ---

function setupRoutes(
    app: Express,
    collection: Collection<MushroomDocument>,
    dependencies: { db: Db, s3Client: S3Client, limiter: Bottleneck, config: typeof config }
): void {
    const { db, s3Client, limiter, config } = dependencies;

    app.get('/api/health', (req, res) => handleHealthCheck(req, res, db));
    app.post('/api/mushrooms', (req, res) => handleFindMushrooms(req, res, collection));
    app.get('/api/mushrooms/:id', (req, res) => handleGetMushroomById(req, res, collection));
    app.get('/api/mushrooms/scientific-name/:name', (req, res) => handleGetMushroomBySciName(req, res, collection));
    app.get('/api/mushrooms/distinct/:field', (req, res) => handleGetDistinctField(req, res, collection));
    app.post('/api/mushrooms/search', (req, res) => handleSearchMushrooms(req, res, collection, config));
    app.post('/api/mushrooms/count', (req, res) => handleCountMushrooms(req, res, collection));

    // Admin Route - SECURE THIS!
    app.post('/api/admin/process-images', (req, res) => handleProcessImages(req, res, collection, s3Client, limiter, config));
}


// --- Server Start ---

(async () => {
    try {
        // Services already initialized (s3Client, limiter) using config
        const { db, collection } = await connectToDatabase(config.mongoUri!, config.dbName!, config.collectionName!);
        const app = createApp(config);
        setupRoutes(app, collection, { db, s3Client, limiter, config }); // Pass dependencies

        app.listen(config.port, () => {
            console.log(`Server running on port ${config.port}`);
            console.log(`Connected to DB: ${config.dbName}, Collection: ${config.collectionName}`);
            if (config.r2PublicUrl) console.log(`R2 Public URL configured: ${config.r2PublicUrl}`);
            else console.warn('R2 Public URL not configured.');
        });

    } catch (error) {
        console.error("Failed to start the server:", error);
        process.exit(1);
    }
})();


// --- Graceful Shutdown ---
process.on('SIGINT', async () => {
    console.log('SIGINT signal received: Shutting down server gracefully.');
    // Add cleanup logic here (e.g., close database connection if client is accessible)
    // Example: if (mongoClientInstance) await mongoClientInstance.close();
    console.log('Server shutdown complete.');
    process.exit(0);
});

process.on('SIGTERM', async () => {
    console.log('SIGTERM signal received: Shutting down server gracefully.');
    // Add cleanup logic here
    console.log('Server shutdown complete.');
    process.exit(0);
});
