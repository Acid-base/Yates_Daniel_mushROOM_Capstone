// backend/src/routes/userRoutes.ts
import express from 'express';
import { 
  createUser, 
  getUserById, 
  getAllUsers, 
  updateUser, 
  deleteUser, 
  login 
} from '../controllers/userController';

const router = express.Router();

// Create a new user
router.post('/', createUser);

// Get a user by ID
router.get('/:id', getUserById);

// Get all users
router.get('/', getAllUsers);
// Update a user
router.put('/:id', updateUser);

// Delete a user
router.delete('/:id', deleteUser);

// Login
router.post('/login', login);

export default router;
