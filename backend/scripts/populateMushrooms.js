const axios = require('axios');
const mongoose = require('mongoose');
require('dotenv').config(); // Load environment variables from .env

// Connect to MongoDB (updated to use MONGODB_URI)
mongoose.connect(process.env.MONGODB_URI, { 
    
})
  .then(() => console.log('Connected to MongoDB'))
  .catch((err) => console.error('Error connecting to MongoDB:', err));

// Define Mongoose schemas
const MushroomSchema = new mongoose.Schema({
  scientificName: String,
  commonName: String,
  family: String,
  genus: String,
  description: String,
  habitat: String,
  images: [
    {
      url: String,
      caption: String,
    },
  ],
});

const ImageSchema = new mongoose.Schema({
  url: String,
  caption: String,
  mushroom: {
    type: mongoose.Schema.Types.ObjectId,
    ref: 'Mushroom',
  },
});

const Mushroom = mongoose.model('Mushroom', MushroomSchema);
const Image = mongoose.model('Image', ImageSchema);

// Function to fetch data from the Mushroom Observer API
async function fetchMushroomData(name, page = 1) {
  try {
    const response = await axios.get(
      `https://mushroomobserver.org/api2/observations`,
      {
        params: {
          format: 'json',
          detail: 'high', // Request high detail level
          text_name: name,
          page: page,
        }
      }
    );
    return response.data;
      } catch (error) {
    console.error(`Error fetching data for ${name} on page ${page}:`, error);
    // Handle the error appropriately, e.g., rethrow for higher-level handling
    throw error;
      }
    }

// Function to process and insert data into MongoDB
async function processAndInsertData(name) {
  try {
    let currentPage = 1;
    let hasMoreResults = true;

    while (hasMoreResults) {
      const data = await fetchMushroomData(name, currentPage);

      // Mushroom Observer API provides results in an array called "results"
      const mushrooms = data.results || [];

      if (mushrooms.length === 0) {
        hasMoreResults = false;
        break;
      }

      for (const mushroomData of mushrooms) {
        const newMushroom = await Mushroom.findOneAndUpdate(
          { scientificName: mushroomData.consensus.name },
          {
            $setOnInsert: { // Only update if the document is newly inserted
              scientificName: mushroomData.consensus.name,
              commonName: mushroomData.consensus.name, // Use scientific if no common
              family: mushroomData.consensus.rank_level > 10 ? mushroomData.consensus.parent.parent.name : "N/A",
              genus: mushroomData.consensus.rank_level > 20 ? mushroomData.consensus.parent.name : "N/A",
              description: mushroomData.description || '',
              habitat: 'Information not available from API', // Update if API provides it
              images: (mushroomData.images || []).map((image) => ({
                url: image.medium_url,
                caption: '',
              })),
    }
          },
          { upsert: true, new: true }
        );

        // Insert Image documents
        for (const imageData of mushroomData.images || []) {
          await Image.findOneAndUpdate(
            { url: imageData.medium_url },
            {
              $setOnInsert: {
                url: imageData.medium_url,
                caption: '',
                mushroom: newMushroom._id,
              },
            },
            { upsert: true }
          );
        }
      }

      currentPage++;
    }

    console.log(`Data for ${name} inserted/updated successfully.`);
  } catch (error) {
    console.error(`Error processing data for ${name}:`, error);
  } finally {
    // Disconnect from MongoDB after processing
    mongoose.disconnect();
  }
}

// Example usage (run the script)
processAndInsertData('Amanita muscaria');
