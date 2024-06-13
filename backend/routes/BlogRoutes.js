const express = require('express');
const router = express.Router(); 
const blogController = require('../controllers/blogController');
const authenticateToken = require('../middleware/auth'); // Assuming you need authentication

// Get all blog posts
router.get('/', async (req, res) => {
  try {
    const blogPosts = await blogController.getAllBlogPosts(); 
    res.json(blogPosts);
  } catch (error) {
    console.error('Error fetching blog posts:', error);
    res.status(500).json({ error: 'Failed to fetch blog posts' });
  }
});

// Example blog routes
router.post('/create', authenticateToken, blogController.createPost); 
router.put('/:postId/update', authenticateToken, blogController.updatePost); 
router.delete('/:postId', authenticateToken, blogController.deletePost); 
module.exports = router; 
