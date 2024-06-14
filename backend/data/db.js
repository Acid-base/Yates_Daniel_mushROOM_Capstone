// db.js
const mongoose = require('mongoose');
const axios = require('axios'); // Assuming you are using axios for fetching data
const { DatabaseError } = require('../middleware/customErrors');
const Mushroom = require('../models/MushroomModel'); // Assuming you have a Mushroom model
const BlogPost = require('../models/BlogPostModel'); // Assuming you have a BlogPost model
const Favorite = require('../models/FavoriteModel'); // Assuming you have a Favorite model
const User = require('../models/UserModel'); // Assuming you have a User model
require('dotenv').config();
const databaseUri = process.env.MONGODB_URI;

let connection; 

async function connectToDatabase() {
  try {
    connection = await mongoose.connect(databaseUri, {
      // ... your mongoose connection options
    });
    console.log('Connected to MongoDB');
    return connection;
  } catch (error) {
    throw new DatabaseError(`MongoDB connection error: ${error.message}`);
  }
}

async function disconnectFromDatabase() {
  try {
    if (connection) {
      await connection.close();
      console.log('Disconnected from MongoDB');
    }
  } catch (error) {
    console.error('Error disconnecting from MongoDB:', error);
  }
}

// Function to fetch and store mushroom data from an external API
const fetchAndStoreMushroomData = async () => {
  try {
    const mushrooms = await axios.get('https://example.com/api/mushrooms'); // Replace with your actual API
    await Mushroom.insertMany(mushrooms.data);
    console.log('Mushroom data fetched and stored successfully.');
  } catch (error) {
    console.error('Error fetching and storing mushroom data:', error);
  }
};

// Seed database with initial data
const seedDatabase = async () => {
  try {
    await connectToDatabase(); // Connect to the database

    // Clear existing data (optional)
    await BlogPost.deleteMany({});
    await Favorite.deleteMany({});
    await Mushroom.deleteMany({});
    await User.deleteMany({});

    // Seed data
    const seedData = {
      users: [
        { name: 'Alice', email: 'alice@example.com', password: 'password123' },
        { name: 'Bob', email: 'bob@example.com', password: 'securepassword' },
      ],
      mushrooms: [
        {
          scientificName: 'Agaricus bisporus',
          commonName: 'Button Mushroom',
          latitude: 40.7128,
          longitude: -74.0060,
          imageUrl: 'https://example.com/agaricus_bisporus.jpg',
          description: 'A common edible mushroom.',
          // ... other mushroom fields
        },
        {
          scientificName: 'Amanita muscaria',
          commonName: 'Fly Agaric',
          latitude: 51.5074,
          longitude: 0.1278,
          imageUrl: 'https://example.com/amanita_muscaria.jpg',
          description: 'A poisonous mushroom with a red cap and white spots.',
          // ... other mushroom fields
        },
      ],
      blogPosts: [
        {
          title: 'Mushroom Hunting Tips',
          author: 'Alice',
          content: 'Learn the basics of mushroom foraging...',
          imageUrl: 'https://example.com/mushroom_hunting.jpg',
        },
        {
          title: 'The Fascinating World of Fungi',
          author: 'Bob',
          content: 'Explore the diverse kingdom of fungi...',
          imageUrl: 'https://example.com/fungi_world.jpg',
        },
      ],
      favorites: [ // You'll need user and mushroom IDs for these
        { userId: 'USER_ID_1', mushroomId: 'MUSHROOM_ID_1' },
        { userId: 'USER_ID_2', mushroomId: 'MUSHROOM_ID_2' },
      ],
    };

    // Insert seed data
    const createdUsers = await User.create(seedData.users);
    const createdMushrooms = await Mushroom.create(seedData.mushrooms);

    // Update favorites with actual IDs
    const updatedFavorites = seedData.favorites.map(favorite => ({
      ...favorite,
      userId: createdUsers.find(user => user.name === 'Alice')._id, // Assuming Alice is the first user
      mushroomId
