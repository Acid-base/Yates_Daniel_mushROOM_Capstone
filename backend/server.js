const express = require('express');
const axios = require('axios');
const mongoose = require('mongoose');
const cors = require('cors');
const rateLimit = require('axios-rate-limit');
require('dotenv').config(); // Load environment variables
const app = express();
const port = process.env.PORT || 3001;
const databaseUri = process.env.MONGODB_URI;

// Rate limiting - Moved declaration outside to avoid creating
// a new instance on each request.
const api = rateLimit(axios.create(), { maxRequests: 1, perMilliseconds: 6000 }); 
// Middleware
app.use(express.json());
app.use(cors());

// MongoDB Connection
mongoose.connect(databaseUri, { 
})
.then(() => console.log('Connected to MongoDB'))
.catch(error => console.error('MongoDB connection error:', error));

// Define your Mushroom schema 
const MushroomSchema = new mongoose.Schema({
  scientificName: { type: String, required: true },
  latitude: { type: Number, required: true }, 
  longitude: { type: Number, required: true },
  imageUrl: String,
  description: String,
  // ... add other relevant fields
});
const Mushroom = mongoose.model('Mushroom', MushroomSchema);
// --- Function to fetch and store mushroom data ---
async function fetchAndStoreMushrooms(page = 1) {
  try {
    const response = await api.get('https://mushroomobserver.org/api2/observations', {
      params: {
        format: 'json',
        detail: 'high', 
        page: page,
      },
      headers: {
        'Authorization': `Bearer ${process.env.MUSHROOM_OBSERVER_API_KEY}` // Use env variable
      },
    });

    const newMushrooms = response.data.results.map(observation => ({
      scientificName: observation.consensus.name || 'N/A',
      latitude: observation.latitude || 0, 
      longitude: observation.longitude || 0,
      imageUrl: observation.primary_image?.medium_url || 'placeholder.jpg', // Optional chaining
      description: observation.description || '',
      // ... map other fields 
    }));

    // Use updateOne with upsert: true to avoid duplicates
    const insertResult = await Mushroom.bulkWrite(newMushrooms.map(mushroom => ({
      updateOne: {
        filter: { scientificName: mushroom.scientificName, latitude: mushroom.latitude, longitude: mushroom.longitude },
        update: { $set: mushroom }, 
        upsert: true 
      }
    })));

    console.log(`Processed ${newMushrooms.length} mushrooms (Inserted: ${insertResult.upsertedCount}, Updated: ${insertResult.modifiedCount}) for page ${page}`);
    console.log(`Processed ${newMushrooms.length} mushrooms (Inserted: ${insertResult.upsertedCount}, Updated: ${insertResult.modifiedCount}) for page ${page}`);
    // Handle pagination
    if (response.data.more) {
      await fetchAndStoreMushrooms(page + 1);
    }
  } catch (error) {
    console.error('Error fetching/storing mushroom data:', error);
  }
}

// Example usage: Fetch data when the server starts
fetchAndStoreMushrooms(1)
  .then(() => console.log("Initial data fetch complete!"))
  .catch(err => console.error("Error during initial data fetch:", err));
// --- API Routes --- 
const router = express.Router();

router.get('/', async (req, res) => {
  const searchTerm = req.query.q || '';
  const page = parseInt(req.query.page) || 1;
  const pageSize = 20; 

  try {
    let query = {};

    if (searchTerm) {
      // Case-insensitive search for commonName or scientificName
      query = { 
        $or: [
          { commonName: { $regex: searchTerm, $options: 'i' } },
          { scientificName: { $regex: searchTerm, $options: 'i' } }
        ]
      };
    }
    const mushrooms = await Mushroom.find(query)
      .skip((page - 1) * pageSize)
      .limit(pageSize);

    const totalMushrooms = await Mushroom.countDocuments(query);
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


// --- Start the server ---
app.listen(port, () => {
  console.log(`Server is running on port: ${port}`);
});
