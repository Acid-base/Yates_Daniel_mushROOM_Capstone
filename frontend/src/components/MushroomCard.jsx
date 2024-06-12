// MushroomCard.jsx 
import React, { useState } from 'react';
import PropTypes from 'prop-types'; // Import PropTypes
import './MushroomCard.css'; 
function MushroomCard({ mushroom, onSelect }) {
  const [showDetails, setShowDetails] = useState(false); 
  const imageUrl = mushroom.primary_image?.medium_url || 'placeholder-image.jpg';

  return (
    <li 
      className="mushroom-card" 
      onMouseEnter={() => setShowDetails(true)}
      onMouseLeave={() => setShowDetails(false)}
      onClick={() => onSelect(mushroom.id)} // Call onSelect with the mushroom ID
    >
      <img src={imageUrl} alt={mushroom.name} /> 
      <h3>{mushroom.name}</h3>

      {showDetails && ( 
        <div className="details-card"> 
          <p><strong>Scientific Name:</strong> {mushroom.scientific_name}</p>
          {/* ... other details can be added here */}
        </div>
      )}
    </li>
  );
}

// Add propTypes to MushroomCard
MushroomCard.propTypes = {
  mushroom: PropTypes.shape({
    id: PropTypes.string.isRequired, // Assuming ID is a string
    name: PropTypes.string.isRequired,
    scientific_name: PropTypes.string.isRequired,
    primary_image: PropTypes.shape({
      medium_url: PropTypes.string
    })
  }).isRequired,
  onSelect: PropTypes.func.isRequired
};
export default MushroomCard;
