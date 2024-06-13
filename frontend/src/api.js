// api.js
const MAX_RETRIES = 5; // Maximum number of retries
const INITIAL_DELAY_MS = 5000; // Initial delay in milliseconds
const RATE_LIMIT_MS = 5000; // Rate limit delay in milliseconds

// Helper function for handling rate limiting
const handleRateLimit = async (apiUrl, retryCount, delay) => {
  console.warn(`Rate limit exceeded (attempt ${retryCount + 1}). Retrying in ${delay / 1000} seconds...`);
  await new Promise((resolve) => setTimeout(resolve, delay));
  return { retryCount: retryCount + 1, delay: delay * 2 }; 
};

// Function to fetch mushroom data
export const fetchMushrooms = async (searchTerm = '', pageNumber = 1) => {
  try {
    const response = await fetch(`https://your-api-base-url.com/mushrooms?q=${searchTerm}&page=${pageNumber}&size=20`);
    if (!response.ok) {
      throw new Error(`HTTP error! status: ${response.status}`);
    }
    const data = await response.json();
    return data;
  } catch (error) {
    console.error('Error fetching data:', error);
    throw error;
  }
};

// Function to fetch details for a single mushroom by ID
export const fetchMushroomDetails = async (mushroomId) => {
  try {
    const apiUrl = `/api/mushrooms/${mushroomId}`;

    const response = await fetch(apiUrl);

    if (!response.ok) {
      if (response.status === 429) {
        // Handle rate limiting for individual details
        await handleRateLimit(apiUrl, 0, RATE_LIMIT_MS); // Reset retryCount and delay
        return await fetchMushroomDetails(mushroomId); 
      } else {
        throw new Error(`API request failed with status: ${response.status}`);
      }
    }

    const data = await response.json();
    return data; 
  } catch (error) {
    console.error('Error fetching mushroom details:', error);
    throw error; 
  }
};