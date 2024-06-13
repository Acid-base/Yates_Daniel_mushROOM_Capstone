// src/components/SearchBar.jsx - A React component for a searchable mushroom database with rate limiting
import React, { useState, useRef, useEffect, useCallback } from 'react';
import ResultsList from './ResultsList'; // Import ResultsList

// Set the rate limit (in milliseconds) - adjust based on API guidelines
const RATE_LIMIT_MS = 5000;
const PAGE_SIZE = 20; // Set a page size for fetching data

const SearchBar = () => {
  const [searchTerm, setSearchTerm] = useState('');
  const [results, setResults] = useState([]);
  const [isLoading, setIsLoading] = useState(false);
  const [currentPage, setCurrentPage] = useState(1);
  const [hasMoreResults, setHasMoreResults] = useState(true);
  // Ref variable to store the timestamp of the last API request.
  const lastRequestTime = useRef(0);
  // State variable to track if the rate limit is exceeded.
  const [rateLimitExceeded, setRateLimitExceeded] = useState(false);

  const fetchMushrooms = useCallback(async () => {
    if (isLoading || rateLimitExceeded) {
      return;
    }

    setIsLoading(true);
    setRateLimitExceeded(false);

    // Check for rate limit
    const now = Date.now();
    if (now - lastRequestTime.current < RATE_LIMIT_MS) {
      setRateLimitExceeded(true);
      return;
    }
    lastRequestTime.current = now;

    try {
      const response = await fetch(
        `https://api.example.com/mushrooms?q=${searchTerm}&page=${currentPage}&size=${PAGE_SIZE}` 
        // Replace 'https://api.example.com/mushrooms' with your actual API endpoint
      );

      if (!response.ok) {
        throw new Error('Network response was not ok');
      }

      const data = await response.json();
      setResults(prevResults => [...prevResults, ...data]);
      setHasMoreResults(data.length === PAGE_SIZE);
      setCurrentPage(prevPage => prevPage + 1);
    } catch (error) {
      console.error('Error fetching mushrooms:', error);
    } finally {
      setIsLoading(false);
    }
  }, [searchTerm, currentPage, isLoading, rateLimitExceeded]);

  useEffect(() => {
    if (searchTerm.trim() !== '') {
      fetchMushrooms();
    } else {
      setResults([]);
      setCurrentPage(1);
      setHasMoreResults(true);
    }
  }, [searchTerm, fetchMushrooms]);

  const handleInputChange = (event) => {
    setSearchTerm(event.target.value);
  };

  const handleScroll = useCallback(() => {
    if (
      window.innerHeight + document.documentElement.scrollTop >=
      document.documentElement.scrollHeight - 100 
      // 100 is a buffer for when the scroll reaches the bottom
    ) {
      fetchMushrooms();
    }
  }, [fetchMushrooms]);

  useEffect(() => {
    window.addEventListener('scroll', handleScroll);
    return () => window.removeEventListener('scroll', handleScroll);
  }, [handleScroll]);

  return (
    <div>
      <h1 className="search-bar-title">Mushroom Search</h1>
      <input
        type="text"
        placeholder="Search for mushrooms..."
        value={searchTerm}
        onChange={handleInputChange}
        className="search-bar-input"
      />
      {rateLimitExceeded && (
        <div className="rate-limit-message">
          Rate limit exceeded. Please try again later.
        </div>
      )}
      <ResultsList results={results} IsLoading={isLoading} />
    </div>
  );
};

export default SearchBar;
