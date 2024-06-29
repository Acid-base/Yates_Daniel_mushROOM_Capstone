// api.js
// Define a constant RATE_LIMIT_MS to represent the rate limit in milliseconds (5 seconds).
const RATE_LIMIT_MS = 5000;

// Define an asynchronous function 'fetchMushrooms' to fetch data from the Mushroom Observer API.
// This function takes two parameters: 'searchTerm' (optional) for filtering results, and 'pageNumber' (defaults to 1).
export const fetchMushrooms = async (searchTerm, pageNumber = 1) => {
  // Wrap the entire function body in a try-catch block to handle potential errors.
  try {
    // Initialize the apiUrl with the base URL of the Mushroom Observer API.
    let apiUrl =
      'https://mushroomobserver.org/api2/observations?format=json&detail=high';

    // Conditionally append the search term to the apiUrl if it's provided.
    if (searchTerm) {
      // Encode the search term to make it URL-safe.
      apiUrl += `&text_name=${encodeURIComponent(searchTerm)}`;
    }

    // Append the page number to the apiUrl for pagination.
    apiUrl += `&page=${pageNumber}`;

    // Use the fetch API to make a GET request to the constructed apiUrl.
    const response = await fetch(apiUrl);

    // Check if the response is not ok (status code outside the range 200-299), indicating an error.
    if (!response.ok) {
      // Specifically handle rate limiting (HTTP status code 429).
      if (response.status === 429) {
        // Log a warning message indicating that the rate limit has been exceeded.
        console.warn('Rate limit exceeded. Retrying in 5 seconds...');
        // Wait for the specified RATE_LIMIT_MS (5 seconds) using a promise and setTimeout.
        await new Promise(resolve => setTimeout(resolve, RATE_LIMIT_MS));
        // Recursively call the fetchMushrooms function to retry the request after the delay.
        return await fetchMushrooms(searchTerm, pageNumber);
        // If it's not a rate limiting error, throw a generic error message.
      } else {
        throw new Error('Something went wrong with the API request!');
      }
    }

    // If the response is ok, parse the response body as JSON and store it in the 'data' variable.
    const data = await response.json();

    // Return the fetched data.
    return data;
  } catch (error) {
    // If any error occurs during the process, log the error to the console.
    console.error('Error fetching data:', error);
    // Re-throw the error to propagate it up the call stack, allowing for error handling at a higher level.
    throw error;
  }
};
