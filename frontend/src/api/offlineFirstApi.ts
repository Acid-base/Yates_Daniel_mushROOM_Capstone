import { Mushroom, MushroomFilter } from '../types/mushroom';
import * as mongoDbApi from './mongodb';
import * as localDb from '../db/localDatabase';

// Network status tracking
let isOnline = navigator.onLine;

// Update online status
window.addEventListener('online', () => {
  isOnline = true;
  syncDataWhenOnline();
});

window.addEventListener('offline', () => {
  isOnline = false;
});

// Initialize the system
export const initializeSystem = async (): Promise<void> => {
  try {
    // Initialize local database
    await localDb.initDatabase();
    
    // If online, try to sync data
    if (isOnline) {
      await syncDataWhenOnline();
    }
  } catch (error) {
    console.error('Error initializing system:', error);
  }
};

// Sync remote data to local storage when online
export const syncDataWhenOnline = async (): Promise<void> => {
  try {
    if (!isOnline) return;
    
    // Check if we already have local data
    const hasData = await localDb.hasLocalData();
    if (hasData) return;
    
    // Fetch all mushrooms (with pagination if needed for large datasets)
    const mushrooms = await mongoDbApi.findMushrooms({}, 1000, 0);
    await localDb.storeMushrooms(mushrooms);
    
    // Sync distinct values for filters
    const fields = ['classification.family', 'regional_distribution.countries', 'regional_distribution.states'];
    for (const field of fields) {
      const values = await mongoDbApi.getDistinctValues(field);
      await localDb.storeDistinctValues(field, values);
    }
    
    console.log('Data synchronized successfully');
  } catch (error) {
    console.error('Error syncing data:', error);
  }
};

// Find mushrooms (works in both online and offline modes)
export const findMushrooms = async (filter: MushroomFilter = {}, limit: number = 10, skip: number = 0): Promise<Mushroom[]> => {
  try {
    if (isOnline) {
      // Online: Use MongoDB API
      const mushrooms = await mongoDbApi.findMushrooms(filter, limit, skip);
      
      // Store results in local database for offline access
      await localDb.storeMushrooms(mushrooms);
      
      return mushrooms;
    } else {
      // Offline: Use local database
      return await localDb.getLocalMushrooms(filter, limit, skip);
    }
  } catch (error) {
    console.error('Error finding mushrooms:', error);
    
    // Fallback to local data if API call fails
    return await localDb.getLocalMushrooms(filter, limit, skip);
  }
};

// Find a single mushroom by ID
export const findMushroomById = async (id: string): Promise<Mushroom | null> => {
  try {
    if (isOnline) {
      // Online: Use MongoDB API
      const mushroom = await mongoDbApi.findMushroomById(id);
      
      // Store result in local database for offline access
      if (mushroom) {
        await localDb.storeMushrooms([mushroom]);
      }
      
      return mushroom;
    } else {
      // Offline: Use local database
      return await localDb.getLocalMushroomById(id);
    }
  } catch (error) {
    console.error(`Error fetching mushroom with ID ${id}:`, error);
    
    // Fallback to local data if API call fails
    return await localDb.getLocalMushroomById(id);
  }
};

// Get distinct values for filtering
export const getDistinctValues = async (field: string): Promise<string[]> => {
  try {
    if (isOnline) {
      // Online: Use MongoDB API
      const values = await mongoDbApi.getDistinctValues(field);
      
      // Store results in local database for offline access
      await localDb.storeDistinctValues(field, values);
      
      return values;
    } else {
      // Offline: Use local database
      return await localDb.getLocalDistinctValues(field);
    }
  } catch (error) {
    console.error(`Error fetching distinct values for ${field}:`, error);
    
    // Fallback to local data if API call fails
    return await localDb.getLocalDistinctValues(field);
  }
};

// Count mushrooms matching a filter
export const countMushrooms = async (filter: MushroomFilter = {}): Promise<number> => {
  try {
    if (isOnline) {
      // Online: Use MongoDB API
      return await mongoDbApi.countMushrooms(filter);
    } else {
      // Offline: Use local database
      return await localDb.countLocalMushrooms(filter);
    }
  } catch (error) {
    console.error('Error counting mushrooms:', error);
    
    // Fallback to local data if API call fails
    return await localDb.countLocalMushrooms(filter);
  }
};
