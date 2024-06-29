// src/components/MushroomSearch.jsx
import React, { useContext, useEffect, useRef, useState } from 'react';
import Error from './Error';
import { MushroomContext } from '../MushroomContext';
import ResultsList from './ResultsList';
import SearchBar from './SearchBar';

function MushroomSearch() {
  const {
    fetchMushrooms, // Use the fetchMushrooms function from the context
    mushrooms,
    error,
    loading,
    selectMushroom,
    currentPage,
    setCurrentPage,
  } = useContext(MushroomContext);

  const [searchQuery, setSearchQuery] = useState('');
  const listBottomRef = useRef(null);
  const [isLoading, setIsLoading] = useState(false);

  const handleSearchChange = newSearchTerm => {
    setSearchQuery(newSearchTerm);
    setCurrentPage(1); // Reset page on new search
    fetchMushrooms(newSearchTerm, 1);
  };

  // Initial fetch
  useEffect(() => {
    fetchMushrooms(searchQuery, currentPage);
  }, [fetchMushrooms, searchQuery, currentPage]);

  // Load more when scrolling
  useEffect(() => {
    const handleScroll = () => {
      if (
        listBottomRef.current &&
        !isLoading &&
        window.innerHeight + window.scrollY >= listBottomRef.current.offsetTop
      ) {
        loadMore();
      }
    };
    window.addEventListener('scroll', handleScroll);
    return () => window.removeEventListener('scroll', handleScroll);
  }, []);

  // Load more data
  const loadMore = async () => {
    setIsLoading(true);
    setCurrentPage(currentPage + 1);
    fetchMushrooms(searchQuery, currentPage + 1);
  };

  return (
    <div>
      <SearchBar onSearchChange={handleSearchChange} />

      {error && <Error message={error} />}

      {loading && <p>Loading...</p>}

      <ResultsList results={mushrooms} onMushroomSelect={selectMushroom} />
      {mushrooms.length > 0 && <li ref={listBottomRef} />}
    </div>
  );
}

export default MushroomSearch;
