import axios from 'axios';
import { Mushroom, MushroomFilter } from '../types/mushroom';

// Backend API configuration
// Use environment variable or default to localhost for development
// The VITE_BACKEND_API_URL already includes '/api' in the .env file
const API_URL = import.meta.env.VITE_BACKEND_API_URL || 'http://localhost:5000/api';

const apiClient = axios.create({
  baseURL: API_URL,
  headers: {
    'Content-Type': 'application/json',
  },
});

// Find mushrooms with optional filtering
export const findMushrooms = async (
  filter: MushroomFilter = {},
  limit: number = 10,
  skip: number = 0
): Promise<Mushroom[]> => {
  try {
    // Updated to match the backend path structure - adding /api is redundant since baseURL already has it
    const response = await apiClient.post('/mushrooms', {
      filter,
      limit,
      skip,
    });

    return response.data as Mushroom[];
  } catch (error) {
    console.error('Error fetching mushrooms:', error);
    throw error;
  }
};

// Find a single mushroom by ID
export const findMushroomById = async (id: string): Promise<Mushroom | null> => {
  try {
    // This endpoint stays the same as it already matches the backend
    const response = await apiClient.get(`/mushrooms/${id}`);
    return response.data as Mushroom;
  } catch (error) {
    console.error(`Error fetching mushroom with ID ${id}:`, error);
    throw error;
  }
};

// Find a mushroom by scientific name
export const findMushroomByScientificName = async (scientificName: string): Promise<Mushroom | null> => {
  try {
    // Updated to match backend endpoint: /api/mushrooms/scientific-name/:name
    const response = await apiClient.get(`/mushrooms/scientific-name/${encodeURIComponent(scientificName)}`);
    return response.data as Mushroom;
  } catch (error) {
    console.error(`Error fetching mushroom with scientific name ${scientificName}:`, error);
    throw error;
  }
};

// Get distinct values for filtering
export const getDistinctValues = async (field: string): Promise<string[]> => {
  try {
    // Updated to match the backend endpoint: /api/mushrooms/distinct/:field
    const response = await apiClient.get(`/mushrooms/distinct/${encodeURIComponent(field)}`);
    return response.data as string[];
  } catch (error) {
    console.error(`Error fetching distinct values for ${field}:`, error);
    throw error;
  }
};

// Count total mushrooms matching a filter
export const countMushrooms = async (filter: MushroomFilter = {}): Promise<number> => {
  try {
    const response = await apiClient.post('/mushrooms/count', { filter });
    return response.data.count as number;
  } catch (error) {
    console.error('Error counting mushrooms:', error);
    throw error;
  }
};
