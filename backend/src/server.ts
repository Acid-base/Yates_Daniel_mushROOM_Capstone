// --- At the top ---
import cors from 'cors';
import dotenv from 'dotenv';
import express, { Request, Response } from 'express';
import { Collection, Db, MongoClient, ObjectId } from 'mongodb';
import path from 'path';
// Load environment variables from .env file in project root
dotenv.config({ path: path.resolve(__dirname, '../../.env') });
// --- Express Setup ---
const app = express();
// Enable CORS with specific options
app.use(
  cors({
    origin: ['http://127.0.0.1:5173', 'http://localhost:5173'], // Allow both localhost and 127.0.0.1
    methods: ['GET', 'POST', 'PUT', 'DELETE', 'OPTIONS'],
    allowedHeaders: ['Content-Type', 'Authorization'],
    credentials: true,
  })
);
app.use(express.json());
// --- Interfaces for Request Bodies ---
interface NameParams {
  name: string;
}

interface FieldParams {
  field: string;
}

interface CountRequestBody {
  filter?: any;
}
interface FindRequestBody {
  filter?: any;
  limit?: number;
  skip?: number;
  sort?: any;
}
interface SearchRequestBody {
  query: string;
  limit?: number;
  skip?: number;
}
interface IdParams {
  id: string;
}
// --- Database Connection ---
const MONGODB_CONNECTION_STRING = process.env.MONGODB_CONNECTION_STRING;
const DB_NAME = process.env.DB_NAME;
const COLLECTION_NAME = process.env.COLLECTION_NAME;
const PORT = process.env.PORT || 5000;

if (!MONGODB_CONNECTION_STRING || !DB_NAME || !COLLECTION_NAME) {
  console.error('Error: Missing MongoDB connection details in .env');
  process.exit(1);
}

let db: Db;
let mushroomCollection: Collection<any>; // Use a more specific type if available

MongoClient.connect(MONGODB_CONNECTION_STRING)
  .then((client) => {
    console.log('Connected successfully to MongoDB');
    db = client.db(DB_NAME);
    mushroomCollection = db.collection(COLLECTION_NAME);
    // Start the Express server only after successful connection
    app.listen(process.env.PORT, () => {
      console.log(`Server running on port ${PORT}`);
    });
  })
  .catch((err) => {
    console.error('Failed to connect to MongoDB', err);
    process.exit(1);
  });

// Add this helper function (or adapt your existing one)
function buildMongoQueryFilter(filter: any = {}): any {
  const queryFilter: any = {};

  if (filter.scientific_name) {
    queryFilter.scientific_name = { $regex: filter.scientific_name, $options: 'i' };
  }

  if (filter.common_name) {
    queryFilter.common_name = { $regex: filter.common_name, $options: 'i' };
  }

  if (filter.family) {
    queryFilter['classification.family'] = { $regex: filter.family, $options: 'i' };
  }

  if (filter.habitat) {
    queryFilter['description.habitat'] = { $regex: filter.habitat, $options: 'i' };
  }

  if (filter.country) {
    queryFilter['regional_distribution.countries'] = filter.country;
  }

  if (filter.state) {
    queryFilter['regional_distribution.states'] = filter.state;
  }

  if (filter.region) {
    queryFilter['regional_distribution.regions'] = filter.region;
  }

  if (filter.uses) {
    queryFilter['description.uses'] = { $regex: filter.uses, $options: 'i' };
  }

  return queryFilter;
}

// --- Modified Route Example (Align path with frontend) ---
// Frontend calls POST /api/mushrooms for finding mushrooms
app.post('/api/mushrooms', async (req: Request<{}, {}, FindRequestBody>, res: Response) => {
  try {
    // Ensure collection is initialized
    if (!mushroomCollection) {
      return res.status(503).json({ error: 'Database not available' });
    }

    const { filter = {}, limit = 10, skip = 0, sort } = req.body;
    const queryFilter = buildMongoQueryFilter(filter); // Your existing helper function is still useful!

    const findCursor = mushroomCollection.find(queryFilter).skip(skip).limit(limit);

    if (sort) {
      findCursor.sort(sort); // Apply sort if provided
    }

    const documents = await findCursor.toArray();

    res.json(documents || []);
  } catch (error: unknown) {
    console.error('Error fetching mushrooms:', error);
    const message = error instanceof Error ? error.message : 'An unknown error occurred';
    res.status(500).json({ error: 'Failed to fetch mushrooms', message });
  }
});

// Add this route for finding mushrooms with filters (can be in addition to your existing route)
app.post('/api/mushrooms/find', async (req: Request<{}, {}, FindRequestBody>, res: Response) => {
  try {
    if (!mushroomCollection) {
      return res.status(503).json({ error: 'Database not available' });
    }

    const { filter = {}, limit = 10, skip = 0, sort } = req.body;
    const queryFilter = buildMongoQueryFilter(filter);

    const findCursor = mushroomCollection.find(queryFilter).skip(skip).limit(limit);

    if (sort) {
      findCursor.sort(sort);
    }

    const documents = await findCursor.toArray();

    res.json(documents || []);
  } catch (error: unknown) {
    console.error('Error fetching mushrooms:', error);
    const message = error instanceof Error ? error.message : 'An unknown error occurred';
    res.status(500).json({ error: 'Failed to fetch mushrooms', message });
  }
});

// --- Modified Route Example for ID (Align path with frontend) ---
// Frontend calls GET /api/mushrooms/:id
app.get('/api/mushrooms/:id', async (req: Request<IdParams>, res: Response) => {
  try {
    if (!mushroomCollection) {
      return res.status(503).json({ error: 'Database not available' });
    }
    const { id } = req.params;
    // Validate ID format if necessary before querying
    if (!ObjectId.isValid(id)) {
      return res.status(400).json({ error: 'Invalid ID format' });
    }

    const document = await mushroomCollection.findOne({ _id: new ObjectId(id) });

    if (!document) {
      return res.status(404).json({ error: 'Mushroom not found' });
    }
    res.json(document);
  } catch (error: unknown) {
    console.error(`Error fetching mushroom with ID ${req.params.id}:`, error);
    const message = error instanceof Error ? error.message : 'An unknown error occurred';
    res.status(500).json({ error: 'Failed to fetch mushroom', message });
  }
});

// Add this route to get mushroom by scientific name
app.get('/api/mushrooms/scientific-name/:name', async (req: Request<NameParams>, res: Response) => {
  try {
    if (!mushroomCollection) {
      return res.status(503).json({ error: 'Database not available' });
    }

    const decodedName = decodeURIComponent(req.params.name);

    const document = await mushroomCollection.findOne({
      scientific_name: decodedName,
    });

    if (!document) {
      return res.status(404).json({ error: 'Mushroom not found' });
    }

    res.json(document);
  } catch (error: unknown) {
    console.error(`Error fetching mushroom with scientific name ${req.params.name}:`, error);
    const message = error instanceof Error ? error.message : 'An unknown error occurred';
    res.status(500).json({ error: 'Failed to fetch mushroom', message });
  }
});

// Add this route to get distinct field values
app.get('/api/mushrooms/distinct/:field', async (req: Request<FieldParams>, res: Response) => {
  try {
    if (!mushroomCollection) {
      return res.status(503).json({ error: 'Database not available' });
    }

    const decodedField = decodeURIComponent(req.params.field);

    // List of allowed fields for distinct queries
    const allowedFields = [
      'scientific_name',
      'common_name',
      'classification.family',
      'description.habitat',
      'regional_distribution.countries',
      'regional_distribution.states',
      'regional_distribution.regions',
      'description.uses',
    ];

    if (!allowedFields.includes(decodedField)) {
      return res.status(400).json({
        error: 'Invalid field',
        message: `Field must be one of: ${allowedFields.join(', ')}`,
      });
    }

    const values = await mushroomCollection.distinct(decodedField);

    res.json(values || []);
  } catch (error: unknown) {
    console.error(`Error fetching distinct values for field ${req.params.field}:`, error);
    const message = error instanceof Error ? error.message : 'An unknown error occurred';
    res.status(500).json({ error: 'Failed to fetch distinct values', message });
  }
});

// --- Full-Text Search with Atlas Search ---
app.post('/api/mushrooms/search', async (req: Request<{}, {}, SearchRequestBody>, res: Response) => {
  try {
    if (!mushroomCollection) {
      return res.status(503).json({ error: 'Database not available' });
    }

    const { query, limit = 10, skip = 0 } = req.body;

    if (!query || typeof query !== 'string' || query.trim() === '') {
      return res.status(400).json({ error: 'Search query is required' });
    }

    // Using MongoDB Atlas Search
    const searchResults = await mushroomCollection
      .aggregate([
        {
          $search: {
            index: 'mushroom_search', // Name of your Atlas Search index
            text: {
              query: query,
              path: {
                wildcard: '*', // Search all indexed fields
                // Alternatively, specify fields: ["scientific_name", "common_name", "description.general"]
              },
            },
          },
        },
        {
          $addFields: {
            searchScore: { $meta: 'searchScore' }, // Add search relevance score to results
          },
        },
        {
          $skip: skip,
        },
        {
          $limit: limit,
        },
      ])
      .toArray();

    res.json(searchResults || []);
  } catch (error: unknown) {
    console.error('Error performing Atlas Search:', error);
    const message = error instanceof Error ? error.message : 'An unknown error occurred';

    // Special error handling for missing search index
    if (error instanceof Error && (error.message.includes('search index') || error.message.includes('$search'))) {
      return res.status(500).json({
        error: 'Atlas Search unavailable',
        message:
          'Search index not configured on the collection. Please create an Atlas Search index named "mushroom_search".',
      });
    }

    res.status(500).json({ error: 'Failed to perform search', message });
  }
});

// Add this route to count mushrooms with filters
app.post('/api/mushrooms/count', async (req: Request<{}, {}, CountRequestBody>, res: Response) => {
  try {
    if (!mushroomCollection) {
      return res.status(503).json({ error: 'Database not available' });
    }

    const { filter = {} } = req.body;
    const queryFilter = buildMongoQueryFilter(filter);

    const count = await mushroomCollection.countDocuments(queryFilter);

    res.json({ count });
  } catch (error: unknown) {
    console.error('Error counting mushrooms:', error);
    const message = error instanceof Error ? error.message : 'An unknown error occurred';
    res.status(500).json({ error: 'Failed to count mushrooms', message });
  }
});

// ... other routes modified similarly ...

// --- Remove Data API specific code ---
// const mongoClient: AxiosInstance = ... (DELETE THIS)
// All mongoClient.post(...) calls need to be replaced

// --- Server Start (moved inside MongoClient.connect().then()) ---
// app.listen(PORT, () => { ... }); // (MOVE THIS)
