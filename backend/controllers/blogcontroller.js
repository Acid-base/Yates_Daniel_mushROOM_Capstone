// controllers/blogController.js (or blogController.cjs)

const BlogPost = require('../../models/BlogPostModel'); // Updated import

// ... other imports

const createPost = async (req, res) => {
  try {
    const { title, author, content, imageUrl } = req.body;
    const newBlogPost = new BlogPost({ title, author, content, imageUrl });
    await newBlogPost.save();
    res.status(201).json({ message: 'Blog post created successfully', blogPost: newBlogPost });
  } catch (error) {
    console.error('Error creating blog post:', error);
    res.status(500).json({ error: 'Failed to create blog post' });
  }
};

const updatePost = async (req, res) => {
  try {
    const { postId } = req.params;
    const { title, author, content, imageUrl } = req.body;
    const updatedBlogPost = await BlogPost.findByIdAndUpdate(postId, { title, author, content, imageUrl }, { new: true });
    if (!updatedBlogPost) {
      return res.status(404).json({ error: 'Blog post not found' });
    }
    res.json({ message: 'Blog post updated successfully', blogPost: updatedBlogPost });
  } catch (error) {
    console.error('Error updating blog post:', error);
    res.status(500).json({ error: 'Failed to update blog post' });
  }
};

const deletePost = async (req, res) => {
  try {
    const { postId } = req.params;
    const deletedBlogPost = await BlogPost.findByIdAndDelete(postId);
    if (!deletedBlogPost) {
      return res.status(404).json({ error: 'Blog post not found' });
    }
    res.json({ message: 'Blog post deleted successfully' });
  } catch (error) {
    console.error('Error deleting blog post:', error);
    res.status(500).json({ error: 'Failed to delete blog post' });
  }
};

module.exports = {
  createPost,
  updatePost,
  deletePost
}; 
