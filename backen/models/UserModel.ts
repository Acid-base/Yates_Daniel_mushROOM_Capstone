// backend/src/models/User.ts

import mongoose, { Model, Schema, Document } from 'mongoose';

// Define the User interface to ensure type safety and consistency
interface IUser extends Document {
  name: string;
  email: string;
  password?: string; // Password is optional for queries
  createdAt: Date;
  updatedAt: Date;
}

// Define the User schema
const UserSchema: Schema = new Schema({
  name: { type: String, required: true },
  email: { type: String, required: true, unique: true },
  password: { type: String }, // Password is optional for queries
  createdAt: { type: Date, default: Date.now },
  updatedAt: { type: Date, default: Date.now },
});

// Pre-save hook to automatically update timestamps
UserSchema.pre('save', function (next) {
  this.updatedAt = Date.now();
  next();
});

// Create the User model
const User: Model<IUser> = mongoose.model<IUser>('User', UserSchema);

export default User;
