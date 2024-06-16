// backend/src/models/Favorite.ts
import mongoose, { Schema, Document } from 'mongoose';
import { IFavorite } from '../types/types';

interface FavoriteDocument extends Document, IFavorite {}

const favoriteSchema: Schema = new Schema({
  userId: { type: String, required: true },
  mushroomId: { type: String, required: true },
  favoritedAt: { type: Date, default: Date.now },
});

const Favorite = mongoose.model<FavoriteDocument>('Favorite', favoriteSchema);

export default Favorite;
