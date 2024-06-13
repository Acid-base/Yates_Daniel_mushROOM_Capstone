// src/components/ResultsList.jsx
import React from 'react';
import { useMushroomContext } from './MushroomContext'; // Adjust import path
import MushroomCard from './MushroomCard';

const ResultsList = () => {
  const { state, selectMushroom, loadMoreResults, hasMoreResults } = useMushroomContext();
  const { mushrooms, loading } = state;

  if (loading) {
    return <div>Loading mushrooms...</div>;
  }

  return (
    <ul>
      {mushrooms.map((mushroom) => (
        <li key={mushroom.id} onClick={() => selectMushroom(mushroom.id)}> 
          <MushroomCard mushroom={mushroom} /> 
        </li>
      ))}
      {hasMoreResults && (
        <button onClick={loadMoreResults}>Load More</button>
      )}
    </ul>
  );
};
export default ResultsList;
