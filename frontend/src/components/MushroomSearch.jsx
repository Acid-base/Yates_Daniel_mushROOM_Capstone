import React, { useState, useEffect, useRef, useContext } from 'react';
import { MushroomContext } from '../MushroomContext';
import SearchBar from './SearchBar';
import ResultsList from './ResultsList';
import Error from './Error';

function MushroomSearch() {
  const {
    fetchMushroomsData,
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

  const handleSearchChange = (newSearchTerm) => {
    setSearchQuery(newSearchTerm);
    setCurrentPage(1); // Reset page on new search
    fetchMushroomsData(newSearchTerm, 1); 
  };

  useEffect(() => {
    // Fetch initial data
    fetchMushroomsData(searchQuery, currentPage);
  }, [fetchMushroomsData, searchQuery, currentPage]); 

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
  }, []); // This is the new dependency array

  const loadMore = async () => {
    setIsLoading(true);
    setCurrentPage(currentPage + 1);
    fetchMushroomsData(searchQuery, currentPage + 1);
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
