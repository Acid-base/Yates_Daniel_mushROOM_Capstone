// frontend/src/components/SearchBar.tsx
import React, { useState, useCallback } from 'react';
import { useQuery } from '@tanstack/react-query';
import ResultsList from './ResultsList';

const RATE_LIMIT_MS = 5000;
const PAGE_SIZE = 20;

const SearchBar: React.FC = () => {
  const [searchTerm, setSearchTerm] = useState('');

  const {
    isLoading,
    error,
    data: results,
    fetchNextPage,
    hasNextPage,
  } = useQuery({
    queryKey: ['mushrooms', searchTerm],
    queryFn: async ({ pageParam = 1 }) => {
      const now = Date.now();
      const timeSinceLastRequest = now - lastRequestTimeRef.current;

      if (timeSinceLastRequest < RATE_LIMIT_MS) {
        await new Promise(resolve =>
          setTimeout(resolve, RATE_LIMIT_MS - timeSinceLastRequest)
        );
      }

      lastRequestTimeRef.current = Date.now();

      const response = await fetch(
        `https://api.example.com/mushrooms?q=${searchTerm}&page=${pageParam}&size=${PAGE_SIZE}`
      );

      if (!response.ok) {
        throw new Error('Network response was not ok');
      }
      return response.json();
    },
    getNextPageParam: (_, pages) => {
      return hasNextPage ? pages.length + 1 : undefined;
    },
  });

  const lastRequestTimeRef = React.useRef(0);

  const handleSearchChange = (newSearchTerm: string) => {
    setSearchTerm(newSearchTerm);
  };

  const loadMore = useCallback(() => {
    if (hasNextPage) {
      fetchNextPage();
    }
  }, [fetchNextPage, hasNextPage]);

  return (
    <div>
      <input
        type="text"
        placeholder="Search mushrooms..."
        value={searchTerm}
        onChange={e => handleSearchChange(e.target.value)}
      />
      {error && <div>Error: {error.message}</div>}
      {isLoading && <div>Loading...</div>}
      <ResultsList results={results?.data || []} onLoadMore={loadMore} />
    </div>
  );
};

export default SearchBar;
