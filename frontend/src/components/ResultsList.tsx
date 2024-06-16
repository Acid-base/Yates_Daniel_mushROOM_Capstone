// ResultsList.tsx
import React from "react";
import { useQuery, useQueryClient } from "@tanstack/react-query";
import MushroomCard from "./MushroomCard";
import axios from "axios"; // Assuming you're using Axios

interface ResultsListProps {
  searchQuery: string; // Pass the search query as a prop
  onMushroomSelect: (mushroom: Mushroom) => void; // Define onMushroomSelect prop
}

const fetchMushrooms = async (searchQuery: string, page: number) => {
  const response = await axios.get("/mushrooms", {
    params: { q: searchQuery, page },
  });
  return response.data;
};

const ResultsList: React.FC<ResultsListProps> = ({
  searchQuery,
  onMushroomSelect,
}) => {
  // Add onMushroomSelect prop
  const queryClient = useQueryClient();
  const {
    data: mushroomsData,
    isLoading,
    error,
    fetchNextPage,
    hasNextPage,
  } = useQuery(
    ["mushrooms", searchQuery],
    ({ queryKey, pageParam = 1 }) => fetchMushrooms(queryKey[1], pageParam), // queryKey[1] is the searchQuery
    {
      getNextPageParam: (lastPage, allPages) => {
        return lastPage.length > 0 ? allPages.length + 1 : undefined;
      },
    },
  );

  if (isLoading) {
    return <div>Loading mushrooms...</div>;
  }

  if (error) {
    return <div>Error loading mushrooms</div>;
  }

  const mushrooms = mushroomsData || []; // Handle case where mushroomsData might be undefined

  return (
    <ul>
      {mushrooms.map((mushroom) => (
        <li key={mushroom.id} onClick={() => onMushroomSelect(mushroom)}>
          <MushroomCard mushroom={mushroom} />
        </li>
      ))}
      {hasNextPage && (
        <button onClick={() => fetchNextPage()} disabled={isLoading}>
          Load More
        </button>
      )}
    </ul>
  );
};

export default ResultsList;
