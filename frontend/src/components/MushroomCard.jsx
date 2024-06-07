// MushroomCard.jsx 
import React, { useState } from 'react';
import './MushroomCard.css'; // Import CSS for styling the hover effect

// Define the functional component `MushroomCard` that accepts a `mushroom` object and `onSelect` function as props.
function MushroomCard({ mushroom, onSelect }) {
  // Use the `useState` hook to manage the visibility of the details card. `showDetails` is initialized to `false`.
  const [showDetails, setShowDetails] = useState(false); 

  // Get the image URL from the `mushroom` object. If `medium_url` is not available, use a placeholder image.
  const imageUrl = mushroom.primary_image?.medium_url || 'placeholder-image.jpg';

  // Return a list item (`<li>`) representing a mushroom card.
  return (
    <li 
      className="mushroom-card" 
      // Show the details card on mouse enter.
      onMouseEnter={() => setShowDetails(true)}
      // Hide the details card on mouse leave.
      onMouseLeave={() => setShowDetails(false)}
      // Call the `onSelect` function (passed from the parent component) with the mushroom's ID when the card is clicked.
      onClick={() => onSelect(mushroom.id)} // Add onClick to handle selection
    >
      {/* Display the mushroom image. */}
      <img src={imageUrl} alt={mushroom.name} /> 
      {/* Display the mushroom name. */}
      <h3>{mushroom.name}</h3>

      {/* Conditionally render the details card if `showDetails` is true. */}
      {showDetails && ( 
        <div className="details-card"> 
          {/* Display the mushroom's scientific name. */}
          <p><strong>Scientific Name:</strong> {mushroom.scientific_name}</p>
          {/* ... other details can be added here */}
        </div>
      )}
    </li>
  );
}

// Export the `MushroomCard` component as the default export.
export default MushroomCard;

