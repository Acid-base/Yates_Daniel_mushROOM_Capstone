// server.js - This file starts your Node.js server and connects to the database

const express = require('express'); // Import Express
const mongoose = require('mongoose'); // Import Mongoose
const app = express(); // Create an Express app
const port = process.env.PORT || 5000; // Use the port from .env or default to 5000
const Mushroom = require('./models/Mushroom'); // Import your model 
const axios = require('axios'); // Import axios for downloading CSV files
const fs = require('fs'); // Import fs for file system operations
const schedule = require('node-schedule'); // Import node-schedule for scheduling tasks

// Import the router for your '/mushrooms' API endpoints
const mushroomsRouter = require('./routes/mushrooms'); 
// Middleware
app.use(express.json()); // Parse JSON request bodies

// Define routes
app.use('/mushrooms', mushroomsRouter); // Use mushroomsRouter for routes starting with '/mushrooms'

// **New GET route for /api/mushrooms:**
app.get('/api/mushrooms', async (req, res) => {
    try {
        const searchTerm = req.query.name || ''; 
        const pageNumber = req.query.page || 1;

        let mushrooms;
        if (searchTerm) {
            mushrooms = await Mushroom.find({ name: { $regex: searchTerm, $options: 'i' } })
                    .skip((pageNumber - 1) * 20)
                    .limit(20);
        } else {
            mushrooms = await Mushroom.find()
                    .skip((pageNumber - 1) * 20)
                    .limit(20);
        }
        res.json(mushrooms);
    } catch (error) {
        // ... (handle errors)
        console.error('Error fetching mushrooms:', error);
        res.status(500).json({ error: 'Failed to retrieve mushrooms' });
    }
});

// Function to update data from MushroomObserver CSVs
async function updateDatabase() {
    try {
        // 1. Download CSV files
        const csvFiles = [
            'observations.csv',
            'images_observations.csv',
            'images.csv',
            'names.csv',
            'name_classifications.csv',
            'name_descriptions.csv',
            'locations.csv',
            'location_descriptions.csv'
        ];

        for (const filename of csvFiles) {
            const response = await axios.get(`https://mushroomobserver.org/${filename}`, {
                responseType: 'arraybuffer'
            });

            fs.writeFileSync(`./data/${filename}`, response.data);
            console.log(`Downloaded ${filename}`);
        }

        // 2. Update the database using your importData function (you need to implement this)
        // Example:
        // for (const filename of csvFiles) {
        //     await importData(`./data/${filename}`); // Assuming you have an importData function
        // }
    } catch (error) {
        console.error('Error updating database:', error);
    }
}
// Connect to your MongoDB database 
mongoose.connect('mongodb://localhost:27017/mushroom_app', { 
   
})
.then(() => {
    console.log('Connected to MongoDB');

    // Schedule the update function using a Node.js scheduler
    // Run updateDatabase every night at 1:00 AM
    schedule.scheduleJob('0 1 * * *', updateDatabase); // cron-like schedule
})
.catch((err) => console.error('Error connecting to MongoDB:', err));
// Start the server
app.listen(port, () => {
  console.log(`Server running on port ${port}`);
});
zzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzz