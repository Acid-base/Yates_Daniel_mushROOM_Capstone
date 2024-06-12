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
  let retryCount = 0;
  let delay = INITIAL_DELAY_MS; 

  while (retryCount < MAX_RETRIES) {
    try {
      let apiUrl = `/api/mushrooms`;

      if (searchTerm) {
        apiUrl += `?name=${encodeURIComponent(searchTerm)}`;
      }

      if (pageNumber > 1) {
        apiUrl += `&page=${pageNumber}`;
      }

      const response = await fetch(apiUrl);

      // Check if the response is valid JSON (check response.ok)
      if (response.ok) {
      const data = await response.json();
      return data;
      } else {
        // Handle non-JSON responses (including 429)
        if (response.status === 429) {
          // Handle rate limiting (you have this already)
          const { retryCount: newRetryCount, delay: newDelay } = await handleRateLimit(apiUrl, retryCount, delay);
          retryCount = newRetryCount;
          delay = newDelay;
          continue; 
        } else {
          // Throw a custom error for non-JSON responses
          throw new Error(`API request failed with status: ${response.status}, Response not JSON`); 
      }
    }

  } catch (error) {
      console.error('Error fetching data:', error);
    throw error; 
  }
  }

  // Throw an error if retries are exceeded
  throw new Error('Maximum retries exceeded. Unable to fetch data.'); 
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