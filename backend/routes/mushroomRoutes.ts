// backend/src/routes/mushroomRoutes.ts
import express from 'express';
import {
  createMushroomController,
  getMushroomsController,
  getMushroomByIdController,
  updateMushroomController,
  deleteMushroomController,
} from '../controllers/mushroomController';

const router = express.Router();

// Create a new mushroom
router.post('/', createMushroomController);

// Get all mushrooms
router.get('/', getMushroomsController);

// Get a mushroom by ID
router.get('/:id', getMushroomByIdController);

// Update a mushroom by ID
router.put('/:id', updateMushroomController);

// Delete a mushroom by ID
router.delete('/:id', deleteMushroomController);

export default router;
