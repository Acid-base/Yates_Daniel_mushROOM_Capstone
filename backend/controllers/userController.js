// userController.js
import User from '../models/UserModel';
import bcryptjs from 'bcryptjs';
import jwt from 'jsonwebtoken';
import Mushroom from '../models/MushroomModel';
const secretKey = 'your_secret_key'; // Replace with a strong secret key

// Function to register a new user
export const registerUser = async (req, res) => {
  try {
    const { name, email, password } = req.body;
    const hashedPassword = await bcryptjs.hash(password, 10); // Hash the password

    const newUser = new User({
      name,
      email,
      password: hashedPassword,
    });

    const savedUser = await newUser.save();

    const token = jwt.sign({ userId: savedUser._id }, secretKey); // Generate JWT token

    res.status(201).json({
      message: 'User registered successfully!',
      user: {
        id: savedUser._id,
        name: savedUser.name,
        email: savedUser.email,
      },
      token,
    });
  } catch (error) {
    console.error('Error registering user:', error);
    if (error.code === 11000) { // Duplicate key error (email)
      res.status(409).json({ error: 'Email already exists' });
    } else {
      res.status(500).json({ error: 'Failed to register user' });
    }
  }
};

// Function to log in a user
export const loginUser = async (req, res) => {
  try {
    const { email, password } = req.body;
    const user = await User.findOne({ email });

    if (!user) {
      return res.status(401).json({ error: 'Invalid credentials' });
    }

    const isValidPassword = await bcryptjs.compare(password, user.password);

    if (!isValidPassword) {
      return res.status(401).json({ error: 'Invalid credentials' });
    }

    const token = jwt.sign({ userId: user._id }, secretKey);

    res.status(200).json({
      message: 'Login successful!',
      user: {
        id: user._id,
        name: user.name,
        email: user.email,
      },
      token,
    });
  } catch (error) {
    console.error('Error logging in user:', error);
    res.status(500).json({ error: 'Failed to log in user' });
  }
};

// Function to get all users (for testing or admin purposes)
export const getUsers = async (req, res) => {
  try {
    const users = await User.find();
    res.json(users);
  } catch (error) {
    console.error('Error fetching users:', error);
    res.status(500).json({ error: 'Failed to fetch users' });
  }
};

// Function to toggle a mushroom as a favorite for the authenticated user
export const toggleFavorite = async (req, res) => {
  try {
    const userId = req.userId; // Get the user ID from the authenticated request
    const mushroomId = req.params.mushroomId; 

    const mushroom = await Mushroom.findById(mushroomId);
    if (!mushroom) {
      return res.status(404).json({ error: 'Mushroom not found' });
    }

    // Check if the user already has this mushroom as a favorite
    const isFavorite = mushroom.favorites.some(favorite => favorite.userId.toString() === userId.toString());

    if (isFavorite) {
      // Remove the favorite
      await Mushroom.findByIdAndUpdate(mushroomId, { 
        $pull: { favorites: { userId: userId } }
      });
      res.status(200).json({ message: 'Removed from favorites' });
    } else {
      // Add the favorite
      await Mushroom.findByIdAndUpdate(mushroomId, { 
        $push: { favorites: { userId: userId } }
      });
      res.status(200).json({ message: 'Added to favorites' });
    }
  } catch (error) {
    console.error('Error toggling favorite:', error);
    res.status(500).json({ error: 'Failed to toggle favorite' });
  }
};

// Function to update a user's profile
export const updateProfile = async (req, res) => {
  try {
    const userId = req.userId; // Get the user ID from the authenticated request
    const { name, email, password, location, avatarUrl, bio } = req.body; // Get all fields

    // Find the user by ID
    const user = await User.findById(userId);

    if (!user) {
      return res.status(404).json({ error: 'User not found' });
    }

    // Update user's information (update all fields, even if empty)
    user.name = name || user.name; // Use existing value if not provided
    user.email = email || user.email;
    user.location = location || user.location;
    user.avatarUrl = avatarUrl || user.avatarUrl;
    user.bio = bio || user.bio;

    // Only hash and update password if provided
    if (password) {
      const hashedPassword = await bcryptjs.hash(password, 10);
      user.password = hashedPassword;
    }

    // Save the updated user
    await user.save();

    // Respond with the updated user information
    res.status(200).json({
      message: 'Profile updated successfully!',
      user: {
        id: user._id,
        name: user.name,
        email: user.email,
        location: user.location,
        avatarUrl: user.avatarUrl,
        bio: user.bio
      },
    });
  } catch (error) {
    console.error('Error updating profile:', error);
    res.status(500).json({ error: 'Failed to update profile' });
  }
};
