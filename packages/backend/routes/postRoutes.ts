// backend/src/routes/postRoutes.ts

import express from 'express';
import { createPost, getPostById, getAllPosts, updatePost, deletePost } from '../controllers/postController';

const router = express.Router();

// Create a new post
router.post('/', createPost);

// Get a post by ID
router.get('/:id', getPostById);

// Get all posts
router.get('/', getAllPosts);

// Update a post
router.put('/:id', updatePost);

// Delete a post
router.delete('/:id', deletePost);

export default router;
