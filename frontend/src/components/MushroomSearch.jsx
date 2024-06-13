// src/components/MushroomSearch.jsx
// src/components/MushroomSearch.jsx
import React, { useState, useEffect, useContext } from 'react';
import { MushroomContext } from './MushroomContext'; // Correct path
import ResultsList from './ResultsList';
import SearchBar from './SearchBar';

const MushroomSearch = () => {
  const {
    fetchMushrooms,
    mushrooms,
    error,
    loading,
    selectMushroom,
  } = useContext(MushroomContext);

  const [searchTerm, setSearchTerm] = useState('');
  const [results, setResults] = useState([]);
  const [hasMoreResults, setHasMoreResults] = useState(false);
  const [currentPage, setCurrentPage] = useState(1);

  useEffect(() => {
    // Initial search or logic based on searchTerm change
    const search = async () => {
      const data = await fetchMushrooms(searchTerm, currentPage);
      setResults(data.mushrooms);
      setHasMoreResults(data.hasMore); // Assuming your API provides this info
    };

    search();
  }, [searchTerm, currentPage]); // Trigger on searchTerm or page change

  const handleLoadMore = () => {
    setCurrentPage(currentPage + 1);
  };

  const handleSearchChange = (term) => {
    setSearchTerm(term);
    setCurrentPage(1);
  };

  return (
    <div>
      <SearchBar onSearch={handleSearchChange} />
      {error && <Error message={error} />}
      {loading && <p>Loading...</p>}
      <ResultsList
        results={results}
        loadMoreResults={hasMoreResults ? handleLoadMore : null}
        hasMoreResults={hasMoreResults}
        onMushroomSelect={selectMushroom}
      />
    </div>
  );
};

export default MushroomSearch;

import Error from './Error';
import Error from './Error';
import { MushroomContext } from './MushroomContext'; // Correct path
import ResultsList from './ResultsList';
import SearchBar from './SearchBar';

function MushroomSearch() {
  const {
    fetchMushrooms,
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
    setCurrentPage(1);
    fetchMushrooms(newSearchTerm, 1);
  };

  useEffect(() => {
    fetchMushrooms(searchQuery, currentPage);
  }, [fetchMushrooms, searchQuery, currentPage]);

  // Define loadMore here, before the useEffect
  const loadMore = async () => {
    setIsLoading(true);
    setCurrentPage(currentPage + 1);
    fetchMushrooms(searchQuery, currentPage + 1);
  };

  // useEffect that uses loadMore
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
  }, [isLoading, loadMore]);
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
