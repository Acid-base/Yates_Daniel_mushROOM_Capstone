// server.js - This file starts your Node.js server and connects to the database

const express = require('express'); // Import Express
const mongoose = require('mongoose'); // Import Mongoose
const app = express(); // Create an Express app
const port = process.env.PORT || 3008; // Use the port from .env or default to 3008

// Import the router for your '/mushrooms' API endpoints
const mushroomsRouter = require('./routes/mushrooms'); 
// Middleware
app.use(express.json()); // Parse JSON request bodies

// Define routes
app.use('/mushrooms', mushroomsRouter); // Use mushroomsRouter for routes starting with '/mushrooms'

// Connect to your MongoDB database (replace placeholders with your info)
mongoose.connect('mongodb://localhost:27017/your-database-name', {

})
.then(() => console.log('Connected to MongoDB Localhost...'))
.catch(err => console.error('Error connecting to MongoDB Localhost:', err));
// Start the server
app.listen(port, () => {
  console.log(`Server running on port ${port}`);
});
