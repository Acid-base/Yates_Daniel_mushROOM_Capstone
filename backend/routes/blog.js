// routes/blog.js
const express = require('express');
const router = express.Router();
const BlogPost = require('../models/BlogPost'); // Import BlogPost model

router.get('/', async (req, res) => {
  try {
    const blogPosts = await BlogPost.find().sort({ date: -1 }); // Sort by date in descending order
    res.json(blogPosts);
  } catch (error) {
    console.error('Error fetching blog posts:', error);
    res.status(500).json({ error: 'Failed to fetch blog posts' });
  }
});

// ... other blog routes
