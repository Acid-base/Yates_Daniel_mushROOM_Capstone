import React, { useState } from 'react';
import './MushroomCard.css'; // Import CSS for styling the hover effect

function MushroomCard({ mushroom, onSelect }) {
  // State to manage the visibility of the details card
  const [showDetails, setShowDetails] = useState(false); 

  // Get the image URL (adjust based on the API response structure)
  const imageUrl = mushroom.primary_image?.medium_url || 'placeholder-image.jpg';

  return (
    <li 
      className="mushroom-card" 
      onMouseEnter={() => setShowDetails(true)}
      onMouseLeave={() => setShowDetails(false)}
      onClick={() => onSelect(mushroom.id)} // Add onClick to handle selection
    >
      <img src={imageUrl} alt={mushroom.name} /> 
      <h3>{mushroom.name}</h3>

      {showDetails && ( 
        <div className="details-card"> 
          {/* Add more details here (adjust based on the API response) */}
          <p><strong>Scientific Name:</strong> {mushroom.scientific_name}</p>
          {/* ... other details */}
        </div>
      )}
    </li>
  );
}

export default MushroomCard;
