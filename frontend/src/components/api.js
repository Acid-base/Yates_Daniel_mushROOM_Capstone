// api.js
const MAX_RETRIES = 5; // Maximum number of retries
const INITIAL_DELAY_MS = 5000; // Initial delay in milliseconds
const RATE_LIMIT_MS = 5000; // Rate limit delay in milliseconds

export const fetchMushrooms = async (searchTerm = '', pageNumber = 1) => {
  let retryCount = 0;
  let delay = INITIAL_DELAY_MS; 

  while (retryCount < MAX_RETRIES) {
    try {
    let apiUrl =
      'https://mushroomobserver.org/api2/observations?format=json&detail=high';

    if (searchTerm) {
      apiUrl += `&text_name=${encodeURIComponent(searchTerm)}`;
    }

    apiUrl += `&page=${pageNumber}`;

    const response = await fetch(apiUrl);

      if (response.status === 429) {
        console.warn(`Rate limit exceeded (attempt ${retryCount + 1}). Retrying in ${delay / 1000} seconds...`);
        await new Promise((resolve) => setTimeout(resolve, delay));
        retryCount++;
        delay *= 2; // Double the delay for each retry
        continue; 
      } else if (!response.ok) {
        throw new Error(`API request failed with status: ${response.status}`);
      } 
    const data = await response.json();
      return data; // Return the data if successful 
  } catch (error) {
    console.error('Error fetching data:', error);
    throw error; 
  }
  }

  throw new Error('Maximum retries exceeded. Unable to fetch data.');
};

// Function to fetch details for a single mushroom by ID
export const fetchMushroomDetails = async (mushroomId) => {
  try {
    const apiUrl = `https://mushroomobserver.org/api2/observations/${mushroomId}?format=json&detail=high`; 
    const response = await fetch(apiUrl);

    if (!response.ok) {
      if (response.status === 429) {
        console.warn('Rate limit exceeded. Retrying in 5 seconds...');
        await new Promise((resolve) => setTimeout(resolve, RATE_LIMIT_MS));
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