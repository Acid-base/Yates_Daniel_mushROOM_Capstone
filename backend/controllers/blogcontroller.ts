import { Request, Response } from 'express';
import BlogPost from '../../models/BlogPostModel';

const createPost = async (req: Request, res: Response) => {
  try {
    const { title, author, content, imageUrl } = req.body;
    const newBlogPost = new BlogPost({ title, author, content, imageUrl });
    await newBlogPost.save();
    res.status(201).json({
      message: 'Blog post created successfully',
      blogPost: newBlogPost,
    });
  } catch (error) {
    console.error('Error creating blog post:', error);
    res.status(500).json({ error: 'Failed to create blog post' });
  }
};

const updatePost = async (req: Request, res: Response) => {
  try {
    const { postId } = req.params;
    const { title, author, content, imageUrl } = req.body;
    const updatedBlogPost = await BlogPost.findByIdAndUpdate(
      postId,
      { title, author, content, imageUrl },
      { new: true },
    );
    if (!updatedBlogPost) {
      return res.status(404).json({ error: 'Blog post not found' });
    }
    res.json({
      message: 'Blog post updated successfully',
      blogPost: updatedBlogPost,
    });
  } catch (error) {
    console.error('Error updating blog post:', error);
    res.status(500).json({ error: 'Failed to update blog post

