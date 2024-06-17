// backend/src/controllers/mushroomController.ts
import { Request, Response } from 'express';
import {
  createMushroom,
  getMushrooms,
  getMushroomById,
  updateMushroom,
  deleteMushroom,
} from '../data/mushroomService';

// Create a new mushroom
export const createMushroomController = async (req: Request, res: Response) => {
  try {
    const newMushroom = await createMushroom(req.body);
    res.status(201).json(newMushroom);
  } catch (error) {
    res.status(500).json({ error: 'Failed to create mushroom' });
  }
};

// Get all mushrooms
export const getMushroomsController = async (req: Request, res: Response) => {
  try {
    const mushrooms = await getMushrooms();
    res.status(200).json(mushrooms);
  } catch (error) {
    res.status(500).json({ error: 'Failed to get mushrooms' });
  }
};

// Get a mushroom by ID
export const getMushroomByIdController = async (req: Request, res: Response) => {
  try {
    const mushroom = await getMushroomById(req.params.id);
    if (!mushroom) {
      return res.status(404).json({ error: 'Mushroom not found' });
    }
    res.status(200).json(mushroom);
  } catch (error) {
    res.status(500).json({ error: 'Failed to get mushroom' });
  }
};

// Update a mushroom by ID
export const updateMushroomController = async (req: Request, res: Response) => {
  try {
    const updatedMushroom = await updateMushroom(req.params.id, req.body);
    if (!updatedMushroom) {
      return res.status(404).json({ error: 'Mushroom not found' });
    }
    res.status(200).json(updatedMushroom);
  } catch (error) {
    res.status(500).json({ error: 'Failed to update mushroom' });
  }
};

// Delete a mushroom by ID
export const deleteMushroomController = async (req: Request, res: Response) => {
  try {
    await deleteMushroom(req.params.id);
    res.status(204).send();
  } catch (error) {
    res.status(500).json({ error: 'Failed to delete mushroom' });
  }
};
