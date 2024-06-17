import mongoose from 'mongoose';
import axios from 'axios';
import { DatabaseError } from '../middleware/customErrors';
import Mushroom from '../models/MushroomModel';
import BlogPost from '../models/postModel';
import Favorite from '../models/faveModel';
import User from '../models/UserModel'; // This now imports the updated User model
import dotenv from 'dotenv';

dotenv.config();

const databaseUri = process.env.MONGODB_URI || 'mongodb://localhost:27017/mydatabase';

let connection: typeof mongoose;

async function connectToDatabase() {
  try {
    connection = await mongoose.connect(databaseUri, {
      useNewUrlParser: true,
      useUnifiedTopology: true,
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
      await connection.disconnect();
      console.log('Disconnected from MongoDB');
    }
  } catch (error) {
    console.error('Error disconnecting from MongoDB:', error);
  }
}

const fetchAndStoreMushroomData = async () => {
  try {
    const mushrooms = await axios.get('https://example.com/api/mushrooms');
    await Mushroom.insertMany(mushrooms.data);
    console.log('Mushroom data fetched and stored successfully.');
  } catch (error) {
    console.error('Error fetching and storing mushroom data:', error);
  }
};

const seedDatabase = async () => {
  try {
    await connectToDatabase();

    await BlogPost.deleteMany({});
    await Favorite.deleteMany({});
    await Mushroom.deleteMany({});
    await User.deleteMany({});

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
        },
        {
          scientificName: 'Amanita muscaria',
          commonName: 'Fly Agaric',
          latitude: 51.5074,
          longitude: 0.1278,
          imageUrl: 'https://example.com/amanita_muscaria.jpg',
          description: 'A poisonous mushroom with a red cap and white spots.',
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
      favorites: [
        { userId: '', mushroomId: '' },
        { userId: '', mushroomId: '' },
      ],
    };

    const createdUsers = await User.create(seedData.users);
    const createdMushrooms = await Mushroom.create(seedData.mushrooms);

    const updatedFavorites = seedData.favorites.map((favorite) => ({
      ...favorite,
      userId: createdUsers.find((user) => user.name === 'Alice')!._id,
      mushroomId: createdMushrooms[0]._id, // Assuming first mushroom
    }));

    await Favorite.create(updatedFavorites);

    await BlogPost.create(seedData.blogPosts);

    console.log('Database seeded successfully.');
  } catch (error) {
    console.error('Error seeding database:', error);
  } finally {
    await disconnectFromDatabase();
  }
};

export { connectToDatabase, disconnectFromDatabase, fetchAndStoreMushroomData, seedDatabase };
