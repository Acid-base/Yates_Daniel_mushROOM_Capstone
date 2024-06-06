// src/components/MushroomSearch.jsx 

import React, { useState, useEffect, useRef } from 'react';
import { fetchMushrooms } from '../api.js';
import MushroomCard from './MushroomCard'; 

function MushroomSearch() {
  const [searchTerm, setSearchTerm] = useState('');
  const [searchResults, setSearchResults] = useState([]);
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState(null);
  const [pageNumber, setPageNumber] = useState(1);
  // Ref for tracking the bottom of the list for infinite scrolling
  const listBottomRef = useRef(null);

  const debounceTimer = useRef(null); 

  // Debounce function to limit API requests
  const debouncedSearch = () => {
    clearTimeout(debounceTimer.current);
    debounceTimer.current = setTimeout(async () => {
      setIsLoading(true); 
      setError(null);
      setPageNumber(1); // Reset page number when search term changes

      try {
        const data = await fetchMushrooms(searchTerm, pageNumber); 
        setSearchResults(data.results); 
      } catch (error) {
        setError(error.message || 'Error fetching data.');
      } finally {
        setIsLoading(false);
      }
    }, 500); 
  };

  // Handle search input changes
  const handleChange = (event) => {
    setSearchTerm(event.target.value);
    debouncedSearch(); 
  };

  // Handle infinite scrolling
  useEffect(() => {
    const handleScroll = () => {
      if (
        listBottomRef.current && 
        !isLoading &&
        window.innerHeight + window.scrollY >=
          listBottomRef.current.offsetTop 
      ) {
        loadMore(); 
      }
    };

    window.addEventListener('scroll', handleScroll);
    return () => window.removeEventListener('scroll', handleScroll);
  }, [isLoading]); 

  // Load more results
  const loadMore = async () => {
    setIsLoading(true); 
    try {
      const nextPage = pageNumber + 1;
      const data = await fetchMushrooms(searchTerm, nextPage); 
      // If there are more results, append them
      if (data.results && data.results.length > 0) {
        setSearchResults([...searchResults, ...data.results]);
        setPageNumber(nextPage);
      }
    } catch (error) {
      setError(error.message || 'Error fetching data.');
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <div>
      <input 
        type="text"
        placeholder="Search mushrooms..."
        value={searchTerm}
        onChange={handleChange}
      />
      {isLoading && <p>Loading...</p>}
      {error && <div className="error">{error}</div>}

      <ul>
        {searchResults.map((mushroom) => (
          <MushroomCard key={mushroom.id} mushroom={mushroom} />
        ))}
      </ul>
      {/* Add a ref to the last list item for infinite scrolling */}
      {searchResults.length > 0 && <li ref={listBottomRef} />}
      {isLoading && <p>Loading more...</p>} 
    </div>
  );
}

export default MushroomSearch;
