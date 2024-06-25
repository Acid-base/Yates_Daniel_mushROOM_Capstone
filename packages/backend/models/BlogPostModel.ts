import mongoose, { Model, Schema, Document } from 'mongoose';

// Define the Post interface to ensure type safety and consistency
interface IBlogPost extends Document {
  title: string;
  content: string;
  author: string;
  createdAt: Date;
  updatedAt: Date;
}

// Define the Post schema
const BlogPostSchema: Schema = new Schema({
  title: { type: String, required: true },
  content: { type: String, required: true },
  author: { type: String, required: true },
  createdAt: { type: Date, default: Date.now },
  updatedAt: { type: Date, default: Date.now },
});

// Create the Post model
const BlogPostModel: Model<IBlogPost> = mongoose.model<IBlogPost>('BlogPost', BlogPostSchema);

export default BlogPostModel;
