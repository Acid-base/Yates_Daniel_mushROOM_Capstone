// backend/src/data/userService.ts
import mongoose from 'mongoose';
import User from '../models/User';

// Create a new user
export async function createUser(userData: any): Promise<User> {
  const newUser = new User(userData);
  return await newUser.save();
}

// Get a user by ID
export async function getUserById(id: string): Promise<User | null> {
  return await User.findById(id);
}

// Get a user by email
export async function getUserByEmail(email: string): Promise<User | null> {
  return await User.findOne({ email });
}

// Update a user by ID
export async function updateUser(id: string, updatedData: any): Promise<User | null> {
  return await User.findByIdAndUpdate(id, updatedData, { new: true });
}

// Delete a user by ID
export async function deleteUser(id: string): Promise<void> {
  await User.findByIdAndDelete(id);
}
