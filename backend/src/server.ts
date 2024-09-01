import express from 'express';
import { MongoClient, ObjectId } from 'mongodb';
import dotenv from 'dotenv';

dotenv.config();

const app = express();
const port = process.env.PORT || 3000;
const mongoUri = process.env.MONGODB_URI || 'mongodb://localhost:27017/mushroom_guide';

let db: any;

const connectToDatabase = async () => {
  const maxRetries = 5;
  let retries = 0;

  while (retries < maxRetries) {
    try {
      const client = await MongoClient.connect(mongoUri);
      db = client.db();
      console.log('Connected to MongoDB');
      return;
    } catch (error) {
      retries++;
      console.error(`Error connecting to MongoDB (attempt ${retries}):`, error);
      await new Promise(resolve => setTimeout(resolve, 2000)); // Wait 2 seconds before retrying
    }
  }

  console.error('Failed to connect to MongoDB after multiple attempts');
  process.exit(1);
};


app.use(express.json());

app.get('/api/mushrooms', async (req, res) => {
  try {
    const { search, family, habitat, page = 1, limit = 10 } = req.query;
    const skip = (Number(page) - 1) * Number(limit);

    const query: any = {};
    if (search) {
      query.text_name = { $regex: search, $options: 'i' };
    }
    if (family) {
      query['classification.family'] = family;
    }
    if (habitat) {
      query['description.habitat'] = { $regex: habitat, $options: 'i' };
    }

    const mushrooms = await db.collection('names').aggregate([
      { $match: query },
      {
        $lookup: {
          from: 'name_descriptions',
          localField: 'id',
          foreignField: 'name_id',
          as: 'description'
        }
      },
      {
        $lookup: {
          from: 'name_classifications',
          localField: 'id',
          foreignField: 'name_id',
          as: 'classification'
        }
      },
      {
        $lookup: {
          from: 'observations',
          localField: 'id',
          foreignField: 'name_id',
          as: 'observations'
        }
      },
      {
        $project: {
          id: 1,
          text_name: 1,
          author: 1,
          rank: 1,
          description: { $arrayElemAt: ['$description', 0] },
          classification: { $arrayElemAt: ['$classification', 0] },
          observation_count: { $size: '$observations' }
        }
      },
      { $skip: skip },
      { $limit: Number(limit) }
    ]).toArray();

    const total = await db.collection('names').countDocuments(query);

    res.json({
      mushrooms,
      total,
      page: Number(page),
      pages: Math.ceil(total / Number(limit))
    });
  } catch (error) {
    console.error('Error fetching mushrooms:', error);
    res.status(500).json({ error: 'Internal server error' });
  }
});

app.get('/api/mushrooms/:id', async (req, res) => {
  try {
    const mushroom = await db.collection('names').aggregate([
      { $match: { id: parseInt(req.params.id) } },
      {
        $lookup: {
          from: 'name_descriptions',
          localField: 'id',
          foreignField: 'name_id',
          as: 'description'
        }
      },
      {
        $lookup: {
          from: 'name_classifications',
          localField: 'id',
          foreignField: 'name_id',
          as: 'classification'
        }
      },
      {
        $lookup: {
          from: 'observations',
          localField: 'id',
          foreignField: 'name_id',
          as: 'observations'
        }
      },
      {
        $lookup: {
          from: 'images',
          localField: 'observations.thumb_image_id',
          foreignField: 'id',
          as: 'images'
        }
      },
      {
        $project: {
          id: 1,
          text_name: 1,
          author: 1,
          rank: 1,
          description: { $arrayElemAt: ['$description', 0] },
          classification: { $arrayElemAt: ['$classification', 0] },
          observations: 1,
          images: 1
        }
      }
    ]).next();

    if (mushroom) {
      res.json(mushroom);
    } else {
      res.status(404).json({ error: 'Mushroom not found' });
    }
  } catch (error) {
    console.error('Error fetching mushroom:', error);
    res.status(500).json({ error: 'Internal server error' });
  }
});

app.get('/api/mushrooms/:id/observations', async (req, res) => {
  try {
    const observations = await db.collection('observations').aggregate([
      { $match: { name_id: parseInt(req.params.id) } },
      {
        $lookup: {
          from: 'locations',
          localField: 'location_id',
          foreignField: 'id',
          as: 'location'
        }
      },
      {
        $project: {
          id: 1,
          when: 1,
          notes: 1,
          location: { $arrayElemAt: ['$location', 0] }
        }
      }
    ]).toArray();

    res.json(observations);
  } catch (error) {
    console.error('Error fetching observations:', error);
    res.status(500).json({ error: 'Internal server error' });
  }
});

connectToDatabase().then(() => {
  app.listen(port, () => {
    console.log(`Server running on port ${port}`);
  });
});