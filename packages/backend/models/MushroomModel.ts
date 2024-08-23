// backend/src/models/Mushroom.ts
import mongoose, { Schema, Document } from 'mongoose';
import { IMushroom } from '../types/types';

interface MushroomDocument extends Document, IMushroom {}

const mushroomSchema: Schema = new Schema({
  scientificName: { type: String, required: true },
  latitude: { type: Number, required: true },
  longitude: { type: Number, required: true },
  imageUrl: { type: String, required: true },
  description: { type: String },
  commonName: { type: String },
  family: { type: String },
  genus: { type: String },
  region: { type: String },
  gallery: [{ url: String, thumbnailUrl: String }],
  kingdom: { type: String },
  phylum: { type: String },
  class: { type: String },
  order: { type: String },
  habitat: { type: String },
  edibility: { type: String },
  distribution: { type: String },
  wikipediaUrl: { type: String },
  mushroomObserverUrl: { type: String },
  favorites: [{ userId: String, favoritedAt: Date }],
});

const Mushroom = mongoose.model<MushroomDocument>('Mushroom', mushroomSchema);

export default Mushroom;
