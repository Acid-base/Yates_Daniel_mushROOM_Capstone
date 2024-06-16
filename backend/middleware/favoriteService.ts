// backend/src/data/favoriteService.ts
import mongoose from 'mongoose';
import Favorite from '../models/Favorite';

// Create a new favorite
export async function createFavorite(favoriteData: any): Promise<Favorite> {
  const newFavorite = new Favorite(favoriteData);
  return await newFavorite.save();
}

// Get all favorites for a user
export async function getFavoritesByUser(userId: string): Promise<Favorite[]> {
  return await Favorite.find({ userId });
}

// Check if a user has favorited a mushroom
export async function hasFavorited(userId: string, mushroomId: string): Promise<boolean> {
  return await Favorite.exists({ userId, mushroomId });
}

// Delete a favorite
export async function deleteFavorite(userId: string, mushroomId: string): Promise<void> {
  await Favorite.deleteOne({ userId, mushroomId });
}
