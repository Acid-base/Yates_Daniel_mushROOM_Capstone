// ResultsList.jsx - A React component to display a list of mushrooms
import React from 'react';
import MushroomCard from './MushroomCard';

function ResultsList({ results, onMushroomSelect }) {
  return (
    <ul>
      {results.map((mushroom) => (
        <li key={mushroom.id}>
          <MushroomCard mushroom={mushroom} onSelect={() => onMushroomSelect(mushroom)} />
        </li>
      ))}
    </ul>
  );
}

export default ResultsList;
