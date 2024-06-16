// frontend/src/components/MushroomSearch.tsx
import React, { useState, useRef, useContext } from "react";
import { useQuery } from "@tanstack/react-query";
import { MushroomContext } from "../App"; // Assuming you have a MushroomContext
import SearchBar from "./SearchBar";
import ResultsList from "./ResultsList";
import Error from "./Error"; // Ensure this path is correct

const MushroomSearch: React.FC = () => {
  const { selectMushroom } = useContext(MushroomContext);
  const [searchQuery, setSearchQuery] = useState("");
  const [currentPage, setCurrentPage] = useState(1);
  const listBottomRef = useRef(null);

  const {
    isLoading,
    error,
    data: mushrooms,
    fetchNextPage,
  } = useQuery({
    queryKey: ["mushrooms", searchQuery, currentPage],
    queryFn: async () => {
      const res = await fetch(
        `https://api.example.com/mushrooms?q=${searchQuery}&page=${currentPage}&size=20`,
      );
      if (!res.ok) {
        throw new Error("Network response was not ok");
      }
      return res.json();
    },
    getNextPageParam: (lastPage, allPages) => {
      // Implement logic to determine if there's a next page
      // For example, check if lastPage.length === PAGE_SIZE
      return lastPage.length === 20 ? allPages.length + 1 : undefined;
    },
  });

  const handleSearchChange = (newSearchTerm: string) => {
    setSearchQuery(newSearchTerm);
    setCurrentPage(1);
  };

  const loadMore = () => {
    fetchNextPage();
  };

  // useEffect that uses loadMore
  React.useEffect(() => {
    const handleScroll = () => {
      if (
        listBottomRef.current &&
        !isLoading &&
        window.innerHeight + window.scrollY >= listBottomRef.current.offsetTop
      ) {
        loadMore();
      }
    };
    window.addEventListener("scroll", handleScroll);
    return () => window.removeEventListener("scroll", handleScroll);
  }, [isLoading, loadMore]);

  return (
    <div>
      <SearchBar onSearchChange={handleSearchChange} />
      {error && <Error message={error.message} />}
      {isLoading && <p>Loading...</p>}
      <ResultsList
        results={mushrooms?.data || []}
        onLoadMore={loadMore}
        onMushroomSelect={selectMushroom}
      />
      {mushrooms?.length > 0 && <li ref={listBottomRef} />}
    </div>
  );
};

export default MushroomSearch;
