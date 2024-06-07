// SearchBar.jsx - A React component for a searchable mushroom database with rate limiting
import React, { useState, useRef, useEffect, useCallback } from 'react';
import ResultsList from './ResultsList'; // Import ResultsList
import PropTypes from 'prop-types'; // Import PropTypes

// Set the rate limit (in milliseconds) - adjust based on API guidelines
const RATE_LIMIT_MS = 5000;
const PAGE_SIZE = 20; // Set a page size for fetching data

// Define a functional component named SearchBar that accepts an onSearchChange function as a prop.
function SearchBar({ onSearchChange }) {
  // State variable to keep track of the search term entered by the user in the input field.
  const [searchTerm, setSearchTerm] = useState('');
  // State variable to store the fetched results.
  const [results, setResults] = useState([]); // Initialize with an empty array
  // State variable to keep track of the current page number.
  const [currentPage, setCurrentPage] = useState(1);
  // State variable to indicate if more results are available.
  const [hasMoreResults, setHasMoreResults] = useState(true);
  // Ref variable to store the timestamp of the last API request.
  const lastRequestTime = useRef(0);
  // State variable to track if the rate limit is exceeded.
  const [rateLimitExceeded, setRateLimitExceeded] = useState(false);
  // Ref variable for the debounce timer.
  const debounceTimer = useRef(null);

  // Debounced search function
  const debouncedSearch = () => {
    clearTimeout(debounceTimer.current);
    debounceTimer.current = setTimeout(async () => {
      // Reset the current page and results.
      setCurrentPage(1);
      setResults([]);
      setRateLimitExceeded(false); // Reset rate limit exceeded state

      // Fetch the first page of results.
      fetchResults();
    }, 500); // Adjust the delay (500ms) as needed
  };

  // Event handler function for changes in the search input field.
  const handleChange = (event) => {
    // Update the searchTerm state with the value entered in the input field.
    setSearchTerm(event.target.value);
    // Call the debounced search function
    debouncedSearch();
  };

  // Event handler function for submitting the search form.
  const handleSubmit = async (event) => {
    // Prevent default form submission behavior (page reload).
    event.preventDefault();
  };

  // Function to fetch results based on the current search term and page.
  const fetchResults = useCallback(async () => {
    try {
      // Construct the API URL for your local MongoDB.
      const apiUrl = `/api/mushrooms?name=${searchTerm}&page=${currentPage}`;
      // Make the fetch request to the constructed API URL.
      const response = await fetch(apiUrl);

      // Check if the response status is not ok (not within the 200-299 range).
      if (!response.ok) {
        // If the response is not ok, throw an error with the status.
        throw new Error(`API request failed with status: ${response.status}`);
      }

      // Parse the response body as JSON.
      const data = await response.json();

      // Check if data.results is an array. If not, handle it accordingly.
      if (Array.isArray(data.results)) {
        setResults((prevResults) => [...prevResults, ...data.results]);
        // Update the hasMoreResults state based on the presence of more results.
        setHasMoreResults(data.results.length === PAGE_SIZE);
        // Call the onSearchChange prop function, passing the fetched results.
        onSearchChange(results);
      } else {
        console.warn('API returned unexpected data format. Assuming empty results.');
        setResults([]); // Return an empty array if results is not an array.
      }
    } catch (error) {
      // Log any errors encountered during the process.
      console.error('Error fetching data:', error);
      // Handle errors appropriately (e.g., display an error message to the user)
    }
  }, [searchTerm, currentPage, onSearchChange, results]); // Depend on search term, currentPage, onSearchChange, and results to trigger fetch on initial render or term change.

  // Function to load more results when scrolling to the bottom of the list.
  const loadMoreResults = async () => {
    // Increment the current page number.
    setCurrentPage((prevPage) => prevPage + 1);
    // Fetch the next page of results.
    fetchResults();
  };

  // Use effect to fetch results on initial render.
  useEffect(() => {
    if (searchTerm) {
      fetchResults();
    }
  }, [searchTerm, fetchResults]); // Depend on search term and fetchResults to trigger fetch on initial render or term change.

  // Render the JSX for the SearchBar component.
  return (
    <div>
      {/* Search form that triggers handleSubmit on submission. */}
      <form onSubmit={handleSubmit}>
        {/* Input field for entering search terms. */}
        <input
          type="text"
          value={searchTerm}
          onChange={handleChange}
          placeholder="Search for a mushroom..."
        />
        {/* Submit button for the search form. */}
        <button type="submit">Search</button>
      </form>
      {/* Display a message if the rate limit is exceeded. */}
      {rateLimitExceeded && <p>Rate limit exceeded. Please try again later.</p>}
      {/* ResultsList component to display search results. */}
      {results.length > 0 && (
        <ResultsList results={results} loadMoreResults={loadMoreResults} hasMoreResults={hasMoreResults} /> 
      )}
    </div>
  );
}

// Add propTypes to SearchBar
SearchBar.propTypes = {
  onSearchChange: PropTypes.func.isRequired,
};
export default SearchBar;
