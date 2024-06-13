// models/BlogPost.js
import mongoose from 'mongoose';

const blogPostSchema = new mongoose.Schema({
  title: {
    type: String,
    required: true
  },
  author: {
    type: String,
    required: true
  },
  content: {
    type: String,
    required: true
  },
  date: {
    type: Date,
    default: Date.now
  },
  imageUrl: {
    type: String,
    default: null
  },
});

export default mongoose.model('BlogPost', blogPostSchema);
