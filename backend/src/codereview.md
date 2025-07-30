I'll review the script and suggest improvements with a focus on functional programming principles and prototypal object usage best practices.

Overall Review
Your script is well-structured with good separation of concerns and error handling. I appreciate your approach of using functional programming concepts by defining separate handler functions and using dependency injection. Here are my observations and suggestions:

Strengths
Good error handling throughout the code
Clear separation of concerns with modular functions
Strong typing with TypeScript interfaces
Proper dependency injection
Comprehensive logging
Areas for Improvement
Let's go through some specific improvements:

1. Pure Functions and Immutability
typescript
function buildMongoQueryFilter(filter: any = {}): any {
    // Currently mutates a new object
}
Let's make this more functionally pure by avoiding mutation:

function buildMongoQueryFilter(filter: any = {}): any {
    // Use object spread to create a new object without mutation
    return {
        ...(filter?.scientific_name ? { scientific_name: { $regex: filter.scientific_name, $options: 'i' } } : {}),
        ...(filter?.common_name ? { common_name: { $regex: filter.common_name, $options: 'i' } } : {}),
        ...(filter?.family ? { 'classification.family': { $regex: filter.family, $options: 'i' } } : {}),
        ...(filter?.habitat ? { 'description.habitat': { $regex: filter.habitat, $options: 'i' } } : {}),
        ...(filter?.country ? { 'regional_distribution.countries': filter.country } : {}),
        ...(filter?.state ? { 'regional_distribution.states': filter.state } : {}),
        ...(filter?.region ? { 'regional_distribution.regions': filter.region } : {}),
        ...(filter?.uses ? { 'description.uses': { $regex: filter.uses, $options: 'i' } } : {})
    };
}

Improved MongoDB Query Builder
Code
2. Type Safety Improvements
The use of any in several places reduces type safety. Let's create more specific types:

// More specific filter interface
interface MushroomFilter {
    scientific_name?: string;
    common_name?: string;
    family?: string;
    habitat?: string;
    country?: string;
    state?: string;
    region?: string;
    uses?: string;
    [key: string]: any; // For flexibility with other fields
}

// Type for query results
interface QueryResult<T> {
    data: T[];
    pagination: {
        skip: number;
        limit: number;
        total: number;
    };
}

// Type for search requests
interface SearchRequestBody {
    query: string;
    limit?: number;
    skip?: number;
}

// Update the function to use these types
function buildMongoQueryFilter(filter: MushroomFilter = {}): Record<string, any> {
    return {
        ...(filter?.scientific_name ? { scientific_name: { $regex: filter.scientific_name, $options: 'i' } } : {}),
        ...(filter?.common_name ? { common_name: { $regex: filter.common_name, $options: 'i' } } : {}),
        ...(filter?.family ? { 'classification.family': { $regex: filter.family, $options: 'i' } } : {}),
        ...(filter?.habitat ? { 'description.habitat': { $regex: filter.habitat, $options: 'i' } } : {}),
        ...(filter?.country ? { 'regional_distribution.countries': filter.country } : {}),
        ...(filter?.state ? { 'regional_distribution.states': filter.state } : {}),
        ...(filter?.region ? { 'regional_distribution.regions': filter.region } : {}),
        ...(filter?.uses ? { 'description.uses': { $regex: filter.uses, $options: 'i' } } : {})
    };
}

Improved Type Definitions
Code
3. Function Composition and Currying
Let's implement a more functional approach to handlers by using currying and composition:


Functional Route Handlers with Currying
Code
// Curried handler factory for dependency injection
const createFindMushroomsHandler = (collection: Collection<MushroomDocument>) =>
    async (req: Request<{}, {}, FindRequestBody>, res: Response): Promise<void> => {
        try {
            const { filter = {}, limit = 10, skip = 0, sort } = req.body;
            const queryFilter = buildMongoQueryFilter(filter);
            const options: FindOptions<MushroomDocument> = { skip, limit };
            if (sort) { options.sort = sort; }

            const [documents, totalCount] = await Promise.all([
                collection.find(queryFilter, options).toArray(),
                collection.countDocuments(queryFilter)
            ]);

            res.json({
                data: documents,
                pagination: { skip, limit, total: totalCount }
            });
        } catch (error) {
            console.error('Error fetching mushrooms:', error);
            const message = error instanceof Error ? error.message : 'An unknown error occurred';
            res.status(500).json({ error: 'Failed to fetch mushrooms', message });
        }
    };

// Example usage in route setup:
function setupRoutes(
    app: Express,
    collection: Collection<MushroomDocument>,
    dependencies: { db: Db, s3Client: S3Client, limiter: Bottleneck, config: typeof config }
): void {
    const { db, s3Client, limiter, config } = dependencies;

    app.get('/api/health', (req, res) => handleHealthCheck(req, res, db));

    // Use the curried handler
    app.post('/api/mushrooms', createFindMushroomsHandler(collection));

    // More routes...
}
4. Error Handling with Monads
Let's introduce a simple Result monad pattern for better error handling:


Result Monad for Error Handling
Code
// Simple Result type for functional error handling
type Result<T, E = Error> =
  | { success: true; value: T }
  | { success: false; error: E };

// Helper functions
const Ok = <T>(value: T): Result<T> => ({ success: true, value });
const Err = <E>(error: E): Result<never, E> => ({ success: false, error });

// Example of using Result monad for fetching images
async function fetchImageWithRateLimitSafe(
    rateLimiter: Bottleneck,
    imageUrl: string
): Promise<Result<Buffer, string>> {
    const waitTime = Math.max(config.rateLimitMinIntervalMs, lastImageFetchRunTime);
    console.log(`Waiting ${waitTime}ms before fetching image ${imageUrl}`);
    const startTime = Date.now();

    try {
        const response = await rateLimiter.schedule(() =>
            axios.get(imageUrl, {
                responseType: 'arraybuffer',
                headers: {
                    'User-Agent': 'mushROOM Field Guide/1.0 (educational project)',
                    'Accept': 'image/jpeg,image/png,image/*'
                },
            })
        );

        const endTime = Date.now();
        lastImageFetchRunTime = endTime - startTime;
        console.log(`Fetched image ${imageUrl} in ${lastImageFetchRunTime}ms`);
        return Ok(Buffer.from(response.data));
    } catch (error) {
        const endTime = Date.now();
        lastImageFetchRunTime = endTime - startTime;
        console.error(`Error fetching image from ${imageUrl} (took ${lastImageFetchRunTime}ms):`, error);
        return Err(`Failed to fetch image: ${error instanceof Error ? error.message : String(error)}`);
    }
}

// Example usage in process function
async function processSingleMushroomImage(
    mushroom: MushroomDocument,
    collection: Collection<MushroomDocument>,
    r2Client: S3Client,
    rateLimiter: Bottleneck,
    appConfig: typeof config
): Promise<void> {
    if (!mushroom?._id) { console.warn("Skipping: Invalid mushroom object."); return; }
    if (!appConfig.r2PublicUrl || !appConfig.r2BucketName) {
        console.warn(`Skipping ${mushroom.scientific_name}: R2 config incomplete.`);
        return;
    }

    const imageUrl = mushroom.image?.url;
    if (!imageUrl || typeof imageUrl !== 'string') {
        console.log(`Skipping ${mushroom.scientific_name}: No valid image URL.`);
        return;
    }

    if (imageUrl.includes(appConfig.r2PublicUrl)) {
        console.log(`Skipping ${mushroom.scientific_name}: Image already in R2.`);
        return;
    }

    console.log(`Processing image for ${mushroom.scientific_name} (${mushroom._id}) from ${imageUrl}`);

    const imageResult = await fetchImageWithRateLimitSafe(rateLimiter, imageUrl);

    if (!imageResult.success) {
        // Handle error case
        const errorMessage = imageResult.error;
        console.error(`Error processing image for ${mushroom.scientific_name} (${mushroom._id}):`, errorMessage);

        try {
            const errorUpdatePayload: UpdateFilter<MushroomDocument> = {
                $set: {
                    'image.processing_error': errorMessage,
                    'image.processing_failed_at': new Date(),
                }
            };
            await collection.updateOne({ _id: mushroom._id }, errorUpdatePayload);
        } catch (updateError) {
            console.error(`Failed to log image processing error for ${mushroom.scientific_name} (${mushroom._id}):`, updateError);
        }
        return;
    }

    // Continue processing with imageResult.value
    const imageBuffer = imageResult.value;

    // Rest of the function...
}
5. Configuration Management
Let's separate configuration validation from loading for better functional separation:


Improved Configuration Management
Code

// Define a proper Config type
interface Config {
    mongoUri: string;
    dbName: string;
    collectionName: string;
    port: string;
    r2Endpoint: string;
    r2AccessKeyId: string;
    r2SecretAccessKey: string;
    r2BucketName: string;
    r2PublicUrl: string;
    rateLimitMinIntervalMs: number;
    rateLimitRequestsPerMinute: number;
    allowedOrigins: string[];
    atlasSearchIndex: string;
}

// Load raw config from environment
function loadEnvConfig(): Partial<Config> {
    dotenv.config({ path: path.resolve(__dirname, '../../.env') });

    return {
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
}

// Validate config and ensure it meets requirements
function validateConfig(rawConfig: Partial<Config>): Result<Config, string> {
    const { mongoUri, dbName, collectionName } = rawConfig;

    if (!mongoUri || !dbName || !collectionName) {
        return Err('Missing critical MongoDB connection details in .env');
    }

    // If we get here, we have what we need for a valid config
    // Cast to full Config type, now that we've validated the required fields
    return Ok(rawConfig as Config);
}

// Compose both functions for complete config loading
function getConfig(): Result<Config, string> {
    const rawConfig = loadEnvConfig();
    return validateConfig(rawConfig);
}

// Usage in main function
(async () => {
    try {
        const configResult = getConfig();
        if (!configResult.success) {
            console.error(`Error: ${configResult.error}`);
            process.exit(1);
        }

        const config = configResult.value;

        // Check optional R2 configs and warn if missing
        if (!config.r2Endpoint || !config.r2AccessKeyId || !config.r2SecretAccessKey || !config.r2BucketName || !config.r2PublicUrl) {
            console.warn('Warning: Missing R2 configuration details in .env. Image processing/uploading might fail.');
        }

        // Continue with the rest of the application startup...
    } catch (error) {
        console.error("Failed to start the server:", error);
        process.exit(1);
    }
})();

6. Improve Rate Limiting with Pure Functions

Functional Rate Limiter
Code
// Create a functional wrapper around the rate limiter
// This removes the global state (lastImageFetchRunTime) and encapsulates it
interface RateLimiterState {
    lastRunTime: number;
    limiter: Bottleneck;
}

// Factory function to create a rate limiter with its state
function createRateLimiter(config: Config): RateLimiterState {
    return {
        lastRunTime: 0,
        limiter: new Bottleneck({
            minTime: config.rateLimitMinIntervalMs,
            maxConcurrent: 1,
            reservoir: config.rateLimitRequestsPerMinute,
            reservoirRefreshAmount: config.rateLimitRequestsPerMinute,
            reservoirRefreshInterval: 60 * 1000,
        })
    };
}

// Function that uses the rate limiter and updates its state
async function fetchWithRateLimit<T>(
    state: RateLimiterState,
    fetcher: () => Promise<T>,
    url: string
): Promise<[T, RateLimiterState]> {
    const waitTime = Math.max(config.rateLimitMinIntervalMs, state.lastRunTime);
    console.log(`Waiting ${waitTime}ms before operation: ${url}`);

    const startTime = Date.now();
    try {
        const result = await state.limiter.schedule(fetcher);
        const endTime = Date.now();

        // Create new state with updated lastRunTime
        const newState = {
            ...state,
            lastRunTime: endTime - startTime
        };

        console.log(`Operation completed in ${newState.lastRunTime}ms: ${url}`);
        return [result, newState];
    } catch (error) {
        const endTime = Date.now();
        const newState = {
            ...state,
            lastRunTime: endTime - startTime
        };

        console.error(`Error (took ${newState.lastRunTime}ms): ${url}`, error);
        throw error;
    }
}

// Example usage:
async function someImageProcessingFunction() {
    // Initial state
    let rateLimiterState = createRateLimiter(config);

    // Process first image
    try {
        const [result1, newState1] = await fetchWithRateLimit(
            rateLimiterState,
            () => axios.get(url1, { responseType: 'arraybuffer' }),
            url1
        );

        // Update state for next operation
        rateLimiterState = newState1;

        // Process second image using updated state
        const [result2, newState2] = await fetchWithRateLimit(
            rateLimiterState,
            () => axios.get(url2, { responseType: 'arraybuffer' }),
            url2
        );

        // Continue with the results...
    } catch (error) {
        console.error("Failed to process images:", error);
    }
}
7. S3/R2 Client Operations as Pure Functions

Functional S3/R2 Operations
Code
// Type for upload params
interface UploadParams {
    client: S3Client;
    bucket: string;
    publicBaseUrl: string;
    buffer: Buffer;
    key: string;
    contentType?: string;
}

// Pure function for uploading to R2
async function uploadToR2({
    client,
    bucket,
    publicBaseUrl,
    buffer,
    key,
    contentType = 'image/jpeg'
}: UploadParams): Promise<Result<string, string>> {
    if (!publicBaseUrl || !key || !bucket) {
        return Err('R2 configuration (bucket, public URL) or upload key is missing.');
    }

    try {
        const command = new PutObjectCommand({
            Bucket: bucket,
            Key: key,
            Body: buffer,
            ContentType: contentType
        });

        await client.send(command);
        return Ok(`${publicBaseUrl}/${key}`);
    } catch (error) {
        const errorMsg = `Failed to upload to R2: ${error instanceof Error ? error.message : String(error)}`;
        console.error(errorMsg);
        return Err(errorMsg);
    }
}

// Type for URL params
interface SignedUrlParams {
    client: S3Client;
    bucket: string;
    key: string;
    expiresIn?: number;
}

// Pure function for getting signed URL
async function getSignedUrl({
    client,
    bucket,
    key,
    expiresIn = 3600
}: SignedUrlParams): Promise<Result<string, string>> {
    try {
        const command = new GetObjectCommand({ Bucket: bucket, Key: key });
        const url = await getSignedUrl(client, command, { expiresIn });
        return Ok(url);
    } catch (error) {
        const errorMsg = `Failed to get signed URL: ${error instanceof Error ? error.message : String(error)}`;
        console.error(errorMsg);
        return Err(errorMsg);
    }
}

// Example usage in the image processing function
async function processSingleMushroomImage(
    mushroom: MushroomDocument,
    collection: Collection<MushroomDocument>,
    r2Client: S3Client,
    rateLimiterState: RateLimiterState,
    appConfig: Config
): Promise<void> {
    // Validation checks...

    // Fetch image with rate limiting
    let newRateLimiterState: RateLimiterState;
    let imageBuffer: Buffer;

    try {
        [imageBuffer, newRateLimiterState] = await fetchWithRateLimit(
            rateLimiterState,
            () => axios.get(imageUrl, {
                responseType: 'arraybuffer',
                headers: {
                    'User-Agent': 'mushROOM Field Guide/1.0 (educational project)',
                    'Accept': 'image/jpeg,image/png,image/*'
                }
            }).then(response => response.data),
            imageUrl
        );
    } catch (error) {
        // Handle error...
        return;
    }

    // Prepare upload params
    const urlParts = imageUrl.split('.');
    const fileExtension = urlParts.length > 1 ? urlParts.pop()?.toLowerCase() || 'jpg' : 'jpg';
    const validExtension = ['jpg', 'jpeg', 'png', 'gif', 'webp'].includes(fileExtension) ? fileExtension : 'jpg';
    const fileName = `mushrooms/${mushroom._id.toString()}-${Date.now()}.${validExtension}`;
    const contentType = `image/${validExtension === 'jpg' ? 'jpeg' : validExtension}`;

    // Upload to R2
    const uploadResult = await uploadToR2({
        client: r2Client,
        bucket: appConfig.r2BucketName,
        publicBaseUrl: appConfig.r2PublicUrl,
        buffer: imageBuffer,
        key: fileName,
        contentType
    });

    if (!uploadResult.success) {
        // Handle upload error
        return;
    }

    const newImageUrl = uploadResult.value;

    // Update database...
}

8. Main Execution Flow
Let's improve the main execution flow with more functional composition:

// Type for app dependencies
interface AppDependencies {
    config: Config;
    db: Db;
    collection: Collection<MushroomDocument>;
    s3Client: S3Client;
    rateLimiterState: RateLimiterState;
}

// Pure function to initialize services
async function initializeServices(config: Config): Promise<Result<AppDependencies, string>> {
    try {
        // Create S3 client
        const s3Client = new S3Client({
            region: 'auto',
            endpoint: config.r2Endpoint,
            credentials: config.r2AccessKeyId && config.r2SecretAccessKey ? {
                accessKeyId: config.r2AccessKeyId,
                secretAccessKey: config.r2SecretAccessKey,
            } : undefined,
        });

        // Create rate limiter
        const rateLimiterState = createRateLimiter(config);

        // Connect to database
        const client = await MongoClient.connect(config.mongoUri);
        console.log('Connected successfully to MongoDB');
        const db = client.db(config.dbName);
        const collection = db.collection<MushroomDocument>(config.collectionName);

        // Return all dependencies
        return Ok({
            config,
            db,
            collection,
            s3Client,
            rateLimiterState
        });
    } catch (error) {
        return Err(`Failed to initialize services: ${error instanceof Error ? error.message : String(error)}`);
    }
}

// Function to create and configure Express app
function createApp(dependencies: AppDependencies): Express {
    const { config } = dependencies;
    const app = express();

    // Configure middleware
    app.use(cors({
        origin: config.allowedOrigins,
        methods: ['GET', 'POST', 'PUT', 'DELETE', 'OPTIONS'],
        allowedHeaders: ['Content-Type', 'Authorization'],
        credentials: true,
    }));
    app.use(express.json());

    // Set up routes
    setupRoutes(app, dependencies);

    return app;
}

// Function to start the server
function startServer(app: Express, port: string): void {
    app.listen(port, () => {
        console.log(`Server running on port ${port}`);
    });

    // Set up graceful shutdown
    setupGracefulShutdown();
}

// Separate function for shutdown logic
function setupGracefulShutdown(): void {
    const shutdown = async (signal: string) => {
        console.log(`${signal} signal received: Shutting down server gracefully.`);
        // Add cleanup logic here
        console.log('Server shutdown complete.');
        process.exit(0);
    };

    process.on('SIGINT', () => shutdown('SIGINT'));
    process.on('SIGTERM', () => shutdown('SIGTERM'));
}

// Main application function
async function startApplication(): Promise<void> {
    try {
        // Get and validate config
        const configResult = getConfig();
        if (!configResult.success) {
            console.error(`Configuration error: ${configResult.error}`);
            process.exit(1);
        }

        const config = configResult.value;

        // Initialize services
        const servicesResult = await initializeServices(config);
        if (!servicesResult.success) {
            console.error(`Service initialization error: ${servicesResult.error}`);
            process.exit(1);
        }

        const dependencies = servicesResult.value;

        // Create and start application
        const app = createApp(dependencies);
        startServer(app, config.port);

        console.log(`Connected to DB: ${config.dbName}, Collection: ${config.collectionName}`);
        if (config.r2PublicUrl) {
            console.log(`R2 Public URL configured: ${config.r2PublicUrl}`);
        } else {
            console.warn('R2 Public URL not configured.');
        }

    } catch (error) {
        console.error("Failed to start the server:", error);
        process.exit(1);
    }
}

// Kick everything off
startApplication();

Improved Main Execution Flow
Code
Summary of Improvements
I've proposed several improvements to the codebase that align with functional programming principles and best practices:

Pure Functions: Made functions like buildMongoQueryFilter pure by avoiding mutations and using object spreading for immutability.
Improved Type Safety: Added more specific types to reduce the use of any and make the code safer.
Function Composition and Currying: Introduced curried functions for route handlers to better separate dependencies from behavior.
Monadic Error Handling: Added a simple Result monad for better error management in a functional style.
Configuration Management: Separated configuration loading from validation for better separation of concerns.
Functional Rate Limiting: Removed global state for rate limiting in favor of explicit state passing.
Pure S3/R2 Operations: Refactored cloud storage operations to be more pure and functional.
Improved Main Flow: Reorganized the main execution flow with better separation of concerns.
These changes should help make your code more:

Predictable: By reducing side effects and mutations
Testable: By isolating dependencies and making functions pure
Maintainable: Through better typing and separation of concerns
Readable: Through clearer function composition patterns
The approach still respects your preference for minimal use of prototypal objects, using them only where necessary for interfacing with libraries and frameworks.

Would you like me to go deeper into any specific area of the code or elaborate on any of these improvements?
