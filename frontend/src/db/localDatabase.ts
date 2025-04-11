import { Mushroom, MushroomFilter } from '../types/mushroom';

// IndexedDB database instance
let db: IDBDatabase;

// Database configuration
const DB_NAME = 'mushroomDB';
const DB_VERSION = 1;
const MUSHROOM_STORE = 'mushrooms';
const DISTINCT_VALUES_STORE = 'distinctValues';

// Initialize the database
export const initDatabase = (): Promise<boolean> => {
  return new Promise((resolve, reject) => {
    const request = indexedDB.open(DB_NAME, DB_VERSION);

    request.onerror = (event) => {
      console.error('IndexedDB error:', event);
      reject(false);
    };

    request.onsuccess = (event) => {
      db = (event.target as IDBOpenDBRequest).result;
      console.log('IndexedDB connection opened successfully');
      resolve(true);
    };

    request.onupgradeneeded = (event) => {
      const database = (event.target as IDBOpenDBRequest).result;

      // Create mushrooms object store
      if (!database.objectStoreNames.contains(MUSHROOM_STORE)) {
        const mushroomStore = database.createObjectStore(MUSHROOM_STORE, {
          keyPath: '_id',
        });

        // Create indexes for common queries
        mushroomStore.createIndex('scientific_name', 'scientific_name', { unique: true });
        mushroomStore.createIndex('common_name', 'common_name', { unique: false });
        mushroomStore.createIndex('family', 'classification.family', { unique: false });
      }

      // Create distinct values store for filter options
      if (!database.objectStoreNames.contains(DISTINCT_VALUES_STORE)) {
        database.createObjectStore(DISTINCT_VALUES_STORE, {
          keyPath: 'field',
        });
      }
    };
  });
};

// Store mushrooms in local database
export const storeMushrooms = (mushrooms: Mushroom[]): Promise<void> => {
  return new Promise((resolve, reject) => {
    const transaction = db.transaction([MUSHROOM_STORE], 'readwrite');
    const store = transaction.objectStore(MUSHROOM_STORE);

    transaction.oncomplete = () => {
      resolve();
    };

    transaction.onerror = (event) => {
      console.error('Error storing mushrooms:', event);
      reject();
    };

    mushrooms.forEach((mushroom) => {
      store.put(mushroom);
    });
  });
};

// Store distinct values for filters
export const storeDistinctValues = (field: string, values: string[]): Promise<void> => {
  return new Promise((resolve, reject) => {
    const transaction = db.transaction([DISTINCT_VALUES_STORE], 'readwrite');
    const store = transaction.objectStore(DISTINCT_VALUES_STORE);

    const request = store.put({ field, values });

    request.onsuccess = () => {
      resolve();
    };

    request.onerror = (event) => {
      console.error(`Error storing distinct values for ${field}:`, event);
      reject();
    };
  });
};

// Retrieve mushrooms with optional filtering
export const getLocalMushrooms = (
  filter: MushroomFilter = {},
  limit: number = 10,
  skip: number = 0
): Promise<Mushroom[]> => {
  return new Promise((resolve, reject) => {
    const transaction = db.transaction([MUSHROOM_STORE], 'readonly');
    const store = transaction.objectStore(MUSHROOM_STORE);
    const mushrooms: Mushroom[] = [];

    // This is a simple implementation - for real-world filtering,
    // you might need a more complex approach or a library like Dexie
    const request = store.openCursor();

    let advanced = false;
    let count = 0;

    request.onsuccess = (event) => {
      const cursor = (event.target as IDBRequest).result;

      if (cursor) {
        if (!advanced && skip > 0) {
          advanced = true;
          cursor.advance(skip);
          return;
        }

        const mushroom = cursor.value as Mushroom;

        // Apply filters (simplified implementation)
        let match = true;

        if (
          filter.scientific_name &&
          !mushroom.scientific_name.toLowerCase().includes(filter.scientific_name.toLowerCase())
        ) {
          match = false;
        }

        const commonName = mushroom.common_name ?? 'Unknown';
        if (filter.common_name && !commonName.toLowerCase().includes(filter.common_name.toLowerCase())) {
          match = false;
        }

        // Add more filter conditions as needed

        if (match) {
          mushrooms.push(mushroom);
          count++;

          if (count >= limit) {
            resolve(mushrooms);
            return;
          }
        }

        cursor.continue();
      } else {
        resolve(mushrooms);
      }
    };

    request.onerror = (event) => {
      console.error('Error fetching local mushrooms:', event);
      reject([]);
    };
  });
};

// Get distinct values for filters
export const getLocalDistinctValues = (field: string): Promise<string[]> => {
  return new Promise((resolve, reject) => {
    const transaction = db.transaction([DISTINCT_VALUES_STORE], 'readonly');
    const store = transaction.objectStore(DISTINCT_VALUES_STORE);

    const request = store.get(field);

    request.onsuccess = () => {
      if (request.result) {
        resolve(request.result.values);
      } else {
        resolve([]);
      }
    };

    request.onerror = (event) => {
      console.error(`Error fetching distinct values for ${field}:`, event);
      reject([]);
    };
  });
};

// Count mushrooms with filters
export const countLocalMushrooms = (filter: MushroomFilter = {}): Promise<number> => {
  return new Promise((resolve, reject) => {
    getLocalMushrooms(filter, Number.MAX_SAFE_INTEGER, 0)
      .then((mushrooms) => {
        resolve(mushrooms.length);
      })
      .catch((error) => {
        console.error('Error counting mushrooms:', error);
        reject(0);
      });
  });
};

// Get a mushroom by ID
export const getLocalMushroomById = (id: string): Promise<Mushroom | null> => {
  return new Promise((resolve, reject) => {
    const transaction = db.transaction([MUSHROOM_STORE], 'readonly');
    const store = transaction.objectStore(MUSHROOM_STORE);

    const request = store.get(id);

    request.onsuccess = () => {
      resolve(request.result || null);
    };

    request.onerror = (event) => {
      console.error(`Error fetching mushroom with ID ${id}:`, event);
      reject(null);
    };
  });
};

// Check if database contains data
export const hasLocalData = (): Promise<boolean> => {
  return new Promise((resolve, reject) => {
    const transaction = db.transaction([MUSHROOM_STORE], 'readonly');
    const store = transaction.objectStore(MUSHROOM_STORE);
    const countRequest = store.count();

    countRequest.onsuccess = () => {
      resolve(countRequest.result > 0);
    };

    countRequest.onerror = (event) => {
      console.error('Error checking for local data:', event);
      reject(false);
    };
  });
};
