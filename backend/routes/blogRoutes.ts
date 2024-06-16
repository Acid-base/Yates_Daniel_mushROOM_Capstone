// routes/blog.js
import express, { Request, Response } from 'express';
import BlogPost from '../../models/BlogPostModel';
const router = express.Router();
router.get('/', async (req: Request, res: Response) => {
  try {
    const blogPosts = await BlogPost.find().sort({ date: -1 });
    res.json(blogPosts);
  } catch (error) {
    console.error('Error fetching blog posts:', error);
    res.status(500).json({ error: 'Failed to fetch blog posts' });
  }
});

// ... other blog routes

export default router;
