// ResultsList.jsx - A React component to display a list of mushrooms
import React from 'react';
import MushroomCard from './MushroomCard';

function ResultsList({ results, onMushroomSelect }) {
  // 'results' prop will be an array of mushroom data
  return (
    <ul>
      {results.map((mushroom) => (
        <MushroomCard key={mushroom.id} mushroom={mushroom} onSelect={onMushroomSelect} />
      ))}
    </ul>
  );
}

export default ResultsList;

