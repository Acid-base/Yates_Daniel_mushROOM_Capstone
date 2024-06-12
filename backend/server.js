const express = require('express');
const axios = require('axios');
const mongoose = require('mongoose');
const cors = require('cors');
const rateLimit = require('axios-rate-limit');

const app = express();
const port = process.env.PORT || 3001;
const databaseUri = 'mongodb://localhost/mushroom-app'; // Replace with your connection string if needed
const mushroomObserverApiKey = process.env.MUSHROOM_OBSERVER_API_KEY; // Use environment variable

// Rate limiting
const api = rateLimit(axios.create(), { maxRequests: 1, perMilliseconds: 5000 });

// Middleware
app.use(express.json());
app.use(cors());

// MongoDB Connection
mongoose.connect(databaseUri, {  })
  .then(() => console.log('Connected to MongoDB'))
  .catch(error => console.error('MongoDB connection error:', error));

// Define your Mushroom schema 
const MushroomSchema = new mongoose.Schema({
  scientificName: { type: String, required: true },
  latitude: { type: Number, required: true },  // Assuming you want to plot on a map
  longitude: { type: Number, required: true },
  imageUrl: String,
  description: String,
  // ... add other relevant fields (e.g., commonName, family, genus)
});

const Mushroom = mongoose.model('Mushroom', MushroomSchema);

// --- Function to fetch and store mushroom data ---
async function fetchAndStoreMushrooms(page = 1) {
  try {
    const response = await api.get('https://mushroomobserver.org/api2/observations', {
      params: {
        format: 'json',
        detail: 'high', // Request high detail level
        page: page,
      },
      headers: {
        'Authorization': `Bearer ${mushroomObserverApiKey}`,
      },
    });

    const newMushrooms = response.data.results.map(observation => ({
      scientificName: observation.consensus.name || 'N/A',
      latitude: observation.latitude || 0, // Provide default or handle missing coordinates
      longitude: observation.longitude || 0,
      imageUrl: observation.primary_image ? observation.primary_image.medium_url : 'placeholder.jpg',
      description: observation.description || '',
      // ... map other relevant fields from the API response
    }));

    // Use updateOne with upsert: true to avoid duplicates
    const insertResult = await Mushroom.bulkWrite(newMushrooms.map(mushroom => ({
      updateOne: {
        filter: { scientificName: mushroom.scientificName, latitude: mushroom.latitude, longitude: mushroom.longitude }, // Unique based on name and location
        update: { $set: mushroom }, // Update if found, otherwise insert
        upsert: true
      }
    })));

    console.log(`Processed ${newMushrooms.length} mushrooms (Inserted: ${insertResult.upsertedCount}, Updated: ${insertResult.modifiedCount}) for page ${page}`);

    // Handle pagination
    if (response.data.more) {
      await fetchAndStoreMushrooms(page + 1);
    }
  } catch (error) {
    console.error('Error fetching or storing mushroom data:', error);
    // Additional error handling 
  }
}

// Example usage: Fetch data when the server starts
fetchAndStoreMushrooms(1)
  .then(() => console.log("Initial data fetch complete!"))
  .catch(err => console.error("Error during initial data fetch:", err));
// --- API Routes (mushrooms.js) --- 

const router = express.Router();

router.get('/', async (req, res) => {
  const searchTerm = req.query.q || '';
  const page = parseInt(req.query.page) || 1;

  try {
    let query = {};

    if (searchTerm) {
      query = {
        $or: [
          { commonName: { $regex: searchTerm, $options: 'i' } },
          { scientificName: { $regex: searchTerm, $options: 'i' } }
        ]
      };
    }

    const pageSize = 20;
    const skip = (page - 1) * pageSize;

    const mushrooms = await Mushroom.find(query)
      .skip(skip)
      .limit(pageSize);

    const totalMushrooms = await Mushroom.countDocuments(query);

    res.json({
      results: mushrooms,
      currentPage: page,
      totalPages: Math.ceil(totalMushrooms / pageSize),
    });

  } catch (error) {
    console.error("Error fetching data:", error);
    res.status(500).json({ error: 'Error fetching data' });
  }
});

// ... (Other routes for getting a single mushroom, etc.) 

// --- Register the router ---
app.use('/api/mushrooms', router);

// --- Start the server ---
app.listen(port, () => {
  console.log(`Server is running on port: ${port}`);
});
