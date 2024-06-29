// backend/src/models/Post.ts

import mongoose, { Model, Schema, Document } from 'mongoose';

// Define the Post interface to ensure type safety and consistency
interface IPost extends Document {
  title: string;
  content: string;
  author: string;
  createdAt: Date;
  updatedAt: Date;
}

// Define the Post schema
const PostSchema: Schema = new Schema({
  title: { type: String, required: true },
  content: { type: String, required: true },
  author: { type: String, required: true },
  createdAt: { type: Date, default: Date.now },
  updatedAt: { type: Date, default: Date.now },
});

// Pre-save hook to automatically update timestamps
PostSchema.pre('save', function (next) {
  this.updatedAt = Date.now();
  next();
});

// Create the Post model
const Post: Model<IPost> = mongoose.model<IPost>('Post', PostSchema);

export default Post;
