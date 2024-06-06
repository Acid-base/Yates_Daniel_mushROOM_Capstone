// api.js
// Constant for rate limiting API requests (5 seconds)
const RATE_LIMIT_MS = 5000;

// Asynchronous function to fetch mushroom data from the API
export const fetchMushrooms = async (searchTerm, pageNumber = 1) => {
  try {
    // Base API URL for Mushroom Observer
    let apiUrl =
      'https://mushroomobserver.org/api2/observations?format=json&detail=high';

    // Adjust API parameter based on search term presence
    if (searchTerm) {
      apiUrl += `&text_name=${encodeURIComponent(searchTerm)}`;
    }

    // Add page number to the URL
    apiUrl += `&page=${pageNumber}`;

    // Fetch data from the constructed API URL
    const response = await fetch(apiUrl);

    // Check if the response status is OK (200-299)
    if (!response.ok) {
      // Handle rate limiting (HTTP status code 429)
      if (response.status === 429) {
        console.warn('Rate limit exceeded. Retrying in 5 seconds...');
        // Wait for 5 seconds before retrying the request
        await new Promise((resolve) => setTimeout(resolve, RATE_LIMIT_MS));
        // Recursively call fetchMushrooms to retry the request
        return await fetchMushrooms(searchTerm, pageNumber);
      } else {
        // Throw an error for other HTTP error statuses
        throw new Error('Something went wrong with the API request!');
      }
    }

    // Parse the response body as JSON
    const data = await response.json();

    // Return the fetched data
    return data;
  } catch (error) {
    // Log the error to the console
    console.error('Error fetching data:', error);
    // Re-throw the error to be handled by the caller
    throw error;
  }
};
