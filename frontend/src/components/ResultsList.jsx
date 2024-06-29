// src/components/ResultsList.jsx - A React component to display a list of mushrooms
import React from 'react';
import PropTypes from 'prop-types'; // Import PropTypes
import MushroomCard from './MushroomCard';

const ResultsList = ({
  results,
  onMushroomSelect,
  loadMoreResults,
  hasMoreResults,
}) => (
  <ul>
    {results.map(mushroom => (
      <li key={mushroom.id} onClick={() => onMushroomSelect(mushroom)}>
        <MushroomCard
          mushroom={mushroom}
          onSelect={() => onMushroomSelect(mushroom)}
        />
      </li>
    ))}
    {hasMoreResults && <button onClick={loadMoreResults}>Load More</button>}
  </ul>
);

ResultsList.propTypes = {
  results: PropTypes.arrayOf(
    PropTypes.shape({
      id: PropTypes.string.isRequired,
      name: PropTypes.string.isRequired,
      scientific_name: PropTypes.string.isRequired,
      primary_image: PropTypes.shape({
        medium_url: PropTypes.string,
      }),
      latitude: PropTypes.number,
      longitude: PropTypes.number,
    })
  ).isRequired,
  onMushroomSelect: PropTypes.func.isRequired,
  loadMoreResults: PropTypes.func.isRequired,
  hasMoreResults: PropTypes.bool.isRequired,
};
export default ResultsList;
