const jwt = require('jsonwebtoken');
const User = require('../models/UserModel');
const Mushroom = require('../models/MushroomModel');
// Register user
const registerUser = async (req, res) => {
  const { name, email, password } = req.body;
  try {
    const existingUser = await User.findOne({ email });
    if (existingUser) {
      return res.status(400).json({ error: 'User already exists' });
    }

    const hashedPassword = await bcrypt.hash(password, 10);
    const newUser = new User({
      name,
      email,
      password: hashedPassword,
    });

    await newUser.save();
    res.status(201).json({ message: 'User registered successfully' });
  } catch (error) {
    console.error('Error registering user:', error);
    res.status(500).json({ error: 'Failed to register user' });
  }
};

// Login user
const loginUser = async (req, res) => {
  const { email, password } = req.body;
  try {
    const user = await User.findOne({ email });
    if (!user) {
      return res.status(400).json({ error: 'Invalid email or password' });
    }

    const isMatch = await bcrypt.compare(password, user.password);
    if (!isMatch) {
      return res.status(400).json({ error: 'Invalid email or password' });
    }

    const token = jwt.sign({ userId: user._id }, process.env.JWT_SECRET, {
      expiresIn: '1h',
    });

    res.json({ token });
  } catch (error) {
    console.error('Error logging in user:', error);
    res.status(500).json({ error: 'Failed to login user' });
  }
};

// Toggle favorite mushroom
const toggleFavorite = async (req, res) => {
  const { mushroomId } = req.params;
  const userId = req.userId;

  try {
    const mushroom = await Mushroom.findById(mushroomId);
    if (!mushroom) {
      return res.status(404).json({ error: 'Mushroom not found' });
    }

    const favoriteIndex = mushroom.favorites.findIndex(
      (fav) => fav.userId.toString() === userId
    );

    if (favoriteIndex !== -1) {
      // If already favorited, remove from favorites
      mushroom.favorites.splice(favoriteIndex, 1);
      await mushroom.save();
      return res.json({ message: 'Removed from favorites' });
    } else {
      // Add to favorites
      mushroom.favorites.push({ userId });
      await mushroom.save();
      return res.json({ message: 'Added to favorites' });
    }
  } catch (error) {
    console.error('Error toggling favorite:', error);
    res.status(500).json({ error: 'Failed to toggle favorite' });
  }
};

// Update User Profile
const updateProfile = async (req, res) => {
  try {
    // ... (existing update logic from UserRoutes.js)
  } catch (error) {
    // ... error handling
  }
};

// Get User Details
const getUserDetails = async (req, res) => {
  try {
    // ... (existing getUserDetails logic from UserRoutes.js) 
  } catch (error) {
    // ... error handling
  }
};

module.exports = {
  registerUser,
  loginUser,
  toggleFavorite,
  updateProfile,
  getUserDetails,
};