// backend/src/data/mushroomService.ts
import mongoose from 'mongoose';
import Mushroom from '../models/Mushroom';

// Create a new mushroom
export async function createMushroom(mushroomData: any): Promise<Mushroom> {
  const newMushroom = new Mushroom(mushroomData);
  return await newMushroom.save();
}

// Get all mushrooms
export async function getMushrooms(): Promise<Mushroom[]> {
  return await Mushroom.find();
}

// Get a mushroom by ID
export async function getMushroomById(id: string): Promise<Mushroom | null> {
  return await Mushroom.findById(id);
}

// Update a mushroom by ID
export async function updateMushroom(id: string, updatedData: any): Promise<Mushroom | null> {
  return await Mushroom.findByIdAndUpdate(id, updatedData, { new: true });
}

// Delete a mushroom by ID
export async function deleteMushroom(id: string): Promise<void> {
  await Mushroom.findByIdAndDelete(id);
}
