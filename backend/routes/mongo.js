const express = require('express');
const axios = require('axios');
const mongoose = require('mongoose');

const app = express();
const apikey = 'YOUR_API_KEY'; // Replace with your actual key
const databaseUri = 'mongodb://localhost/mushroom-app'; // Replace with your MongoDB connection string

mongoose.connect(databaseUri, { useNewUrlParser: true, useUnifiedTopology: true })
  .then(() => console.log('Connected to MongoDB'))
  .catch(error => console.error('MongoDB connection error:', error));

// Define a schema for your MongoDB data (example)
const ObservationSchema = new mongoose.Schema({
  // Fields for storing observation data from the API
  // (e.g., species name, observation date, image URLs, etc.)
});

const Observation = mongoose.model('Observation', ObservationSchema);

app.get('/api/observations', async (req, res) => {
  try {
    const response = await axios.get('https://mushroomobserver.org/api/v1/observations', {
      headers: {
        'Authorization': `Bearer ${apikey}`,
      },
    });

    // Process the response data (extract relevant fields)
    const observations = response.data.results.map(observation => {
      // Create a new observation object with selected data
      return {
        // ...relevant fields 
      };
    });

    // Store the data in MongoDB
    await Observation.insertMany(observations);

    res.json({ message: 'Observations fetched and stored' });
  } catch (error) {
    console.error('Error fetching observations:', error);
    res.status(500).json({ error: 'Failed to fetch observations' });
  }
});

app.listen(3000, () => console.log('Server listening on port 3000'));
