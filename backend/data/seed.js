const mongoose = require('mongoose');
const BlogPost = require('./models/BlogPostModel');
const Favorite = require('./models/FavoriteModel');
const Mushroom = require('./models/MushroomModel');
const User = require('./models/UserModel');

require('dotenv').config(); // Load environment variables from .env

const databaseUri = process.env.MONGODB_URI;

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

async function seedDatabase() {
  try {
    await mongoose.connect(databaseUri, {
      useNewUrlParser: true,
      useUnifiedTopology: true,
    });

    // Clear existing data (optional)
    await BlogPost.deleteMany({});
    await Favorite.deleteMany({});
    await Mushroom.deleteMany({});
    await User.deleteMany({});

    // Insert seed data
    const createdUsers = await User.create(seedData.users);
    const createdMushrooms = await Mushroom.create(seedData.mushrooms);

    // Update favorites with actual IDs
    const updatedFavorites = seedData.favorites.map(favorite => ({
      ...favorite,
      userId: createdUsers.find(user => user.name === 'Alice')._id, // Assuming Alice is the first user
      mushroomId: createdMushrooms[0]._id, // Assuming the first mushroom
    }));
    await Favorite.create(updatedFavorites);

    await BlogPost.create(seedData.blogPosts);

    console.log('Database seeded successfully!');
  } catch (error) {
    console.error('Error seeding database:', error);
  } finally {
    mongoose.disconnect();
  }
}

seedDatabase();
