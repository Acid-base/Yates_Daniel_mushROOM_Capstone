// src/components/MushroomSearch.jsx 

import React, { useState, useEffect, useRef } from 'react';
// import { fetchMushrooms } from './api.js'; // No longer needed
import MushroomCard from './MushroomCard'; 

function MushroomSearch() {
  // State variable to store the current search term entered by the user.
  const [searchTerm, setSearchTerm] = useState('');
  // State variable to store the array of mushroom results retrieved from the API.
  const [searchResults, setSearchResults] = useState([]);
  // State variable to track whether the data is currently being fetched from the API.
  const [isLoading, setIsLoading] = useState(false);
  // State variable to store any error message that occurs during the data fetching process.
  const [error, setError] = useState(null);
  // State variable to keep track of the current page number for pagination.
  const [pageNumber, setPageNumber] = useState(1);
  // Ref to store a reference to the last item in the results list for infinite scrolling.
  const listBottomRef = useRef(null);
  // Ref to store the timeout ID for the debounce function, used for rate limiting API calls.
  const debounceTimer = useRef(null); 

  // Function to perform a debounced search, limiting the rate of API calls.
  const debouncedSearch = () => {
    // Clear any existing timeout to prevent immediate API calls on every keystroke.
    clearTimeout(debounceTimer.current);
    // Set a new timeout that will call the API after a delay (500ms in this case).
    debounceTimer.current = setTimeout(async () => {
      // Set loading state to true to indicate data fetching is in progress.
      setIsLoading(true); 
      // Clear any previous errors.
      setError(null);
      // Reset the page number to 1 when the search term changes.
      setPageNumber(1); 

      // Use a try-catch block to handle potential errors during the API call.
      try {
        // Fetch data from the MushroomObserver API 
        const response = await fetch(`/api/mushroomobserver/observations?format=json&detail=high&name=${searchTerm}&page=${pageNumber}`);
        const data = await response.json(); // Parse the response as JSON
        // Update the search results state with the fetched data.
        setSearchResults(data.results); 
      } catch (error) {
        // If an error occurs during the API call, set the error state with the error message.
        setError(error.message || 'Error fetching data.');
      } finally {
        // Finally, set the loading state to false to indicate data fetching is complete.
        setIsLoading(false);
      }
    }, 500); 
  };

  // Event handler for input changes in the search bar.
  const handleChange = (event) => {
    // Update the search term state with the current value of the input field.
    setSearchTerm(event.target.value);
    // Call the debouncedSearch function to initiate a new search after a delay.
    debouncedSearch(); 
  };

  // useEffect hook to set up an event listener for scrolling.
  useEffect(() => {
    // Function to handle scroll events.
    const handleScroll = () => {
      // Check if the listBottomRef has been set and the data is not currently being loaded.
      if (
        listBottomRef.current && 
        !isLoading &&
        // Check if the user has scrolled to the bottom of the list.
        window.innerHeight + window.scrollY >=
          listBottomRef.current.offsetTop 
      ) {
        // If all conditions are met, call the loadMore function to fetch the next page of results.
        loadMore(); 
      }
    };

    // Attach the handleScroll event listener to the window's scroll event.
    window.addEventListener('scroll', handleScroll);
    // Cleanup function to remove the event listener when the component unmounts.
    return () => window.removeEventListener('scroll', handleScroll);
  }, [isLoading]); 

  // Function to load more results when the user scrolls to the bottom of the list.
  const loadMore = async () => {
    // Set loading state to true to indicate data fetching is in progress.
    setIsLoading(true); 
    // Use a try-catch block to handle potential errors during the API call.
    try {
      // Increment the page number to fetch the next page.
      const nextPage = pageNumber + 1;
      // Call the fetchMushrooms function from the API to retrieve the next page of results.
      const response = await fetch(`/api/mushroomobserver/observations?format=json&detail=high&name=${searchTerm}&page=${nextPage}`);
      const data = await response.json(); // Parse the response as JSON
      // Check if there are more results to load.
      if (data.results && data.results.length > 0) {
        // If there are more results, append them to the existing search results state.
        setSearchResults([...searchResults, ...data.results]);
        // Update the page number state to reflect the loaded page.
        setPageNumber(nextPage);
      }
    } catch (error) {
      // If an error occurs during the API call, set the error state with the error message.
      setError(error.message || 'Error fetching data.');
    } finally {
      // Finally, set the loading state to false to indicate data fetching is complete.
      setIsLoading(false);
    }
  };

  // JSX rendering of the MushroomSearch component.
  return (
    <div>
      {/* Input field for the search term. */}
      <input 
        type="text"
        placeholder="Search mushrooms..."
        value={searchTerm}
        onChange={handleChange}
      />
      {/* Display "Loading..." message while data is being fetched. */}
      {isLoading && <p>Loading...</p>}
      {/* Display any errors that occur during data fetching. */}
      {error && <div className="error">{error}</div>}

      {/* Display the list of mushroom results. */}
      <ul>
        {searchResults.map((mushroom) => (
          <MushroomCard key={mushroom.id} mushroom={mushroom} />
        ))}
      </ul>
      {/* Add a ref to the last list item for infinite scrolling */}
      {searchResults.length > 0 && <li ref={listBottomRef} />}
      {/* Display "Loading more..." while more data is being fetched. */}
      {isLoading && <p>Loading more...</p>} 
    </div>
  );
}

// Export the MushroomSearch component as the default export.
export default MushroomSearch;
