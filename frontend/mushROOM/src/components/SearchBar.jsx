// SearchBar.jsx - A React component for a searchable mushroom database with rate limiting
import React, { useState, useRef } from 'react';
import ResultsList from './ResultsList'; // Import ResultsList

// Set the rate limit (in milliseconds) - adjust based on API guidelines
const RATE_LIMIT_MS = 5000;

const fetchMushrooms = async (searchTerm, pageNumber = 1) => {
  try {
    let apiUrl = 'https://mushroomobserver.org/api2/observations?format=json&detail=high';

    if (searchTerm) {
      apiUrl += `&name=${encodeURIComponent(searchTerm)}`;
    }

    apiUrl += `&page=${pageNumber}`;

    const response = await fetch(apiUrl);

    if (!response.ok) {
      throw new Error(`API request failed with status: ${response.status}`);
    }

    const data = await response.json();
    return data;
  } catch (error) {
    console.error('Error fetching data:', error);
    // Handle errors appropriately (e.g., display an error message to the user)
  }
};

function SearchBar({ onSearchChange }) { // Receive onSearchChange as a prop
  const [searchTerm, setSearchTerm] = useState('');
  const lastRequestTime = useRef(0); // Track the last request time to enforce rate limiting
  // Removed searchResults state
  const handleChange = (event) => {
    setSearchTerm(event.target.value);
  };

  const handleSubmit = async (event) => {
    event.preventDefault();

    const currentTime = Date.now();
    const timeSinceLastRequest = currentTime - lastRequestTime.current;

    if (timeSinceLastRequest >= RATE_LIMIT_MS) {
      lastRequestTime.current = currentTime; // Update last request time

      try {
        const data = await fetchMushrooms(searchTerm);
        onSearchChange(data.results || []); // Pass results to App.jsx
      } catch (error) {
        console.error('Error fetching data:', error);
      }
    } else {
      // Handle rate limit: Display a message, implement a retry mechanism, etc.
      console.warn('Rate limit exceeded. Please try again later.');
    }
  };

  return (
    <div>
      <form onSubmit={handleSubmit}>
        <input
          type="text"
          value={searchTerm}
          onChange={handleChange}
          placeholder="Search for a mushroom..."
        />
        <button type="submit">Search</button>
      </form>
      <ResultsList results={[]} /> {/* ResultsList will now be managed in a parent component */} 
    </div>
  );
}

export default SearchBar;
