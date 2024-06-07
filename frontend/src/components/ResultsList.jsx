// ResultsList.jsx - A React component to display a list of mushrooms
import React from 'react';
import MushroomCard from './MushroomCard';

function ResultsList({ results, onMushroomSelect }) {
  if (!results) { 
    return <div>Loading mushrooms...</div>; 
  }
  return (
    <ul>
      {results.map((mushroom) => (
        <MushroomCard key={mushroom.id} mushroom={mushroom} onSelect={onMushroomSelect} />
      ))}
    </ul>
  );
}

export default ResultsList;
