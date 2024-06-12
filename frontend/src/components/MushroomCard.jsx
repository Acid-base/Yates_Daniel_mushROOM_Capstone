// MushroomCard.jsx 
import React, { useState, useEffect } from 'react';
import PropTypes from 'prop-types'; // Import PropTypes
import './MushroomCard.css'; 
function MushroomCard({ mushroom, onSelect }) {
  const [showDetails, setShowDetails] = useState(false); 
  const [isFavorite, setIsFavorite] = useState(false); // Track if the mushroom is favorited
  const [region, setRegion] = useState('Unknown'); // State for region
  const imageUrl = mushroom.primary_image?.medium_url || 'placeholder-image.jpg';

  useEffect(() => {
    // Load favorite status from local storage or set default
    const savedFavorites = JSON.parse(localStorage.getItem('favorites')) || [];
    setIsFavorite(savedFavorites.includes(mushroom.id));
  }, [mushroom.id]);

  useEffect(() => {
    // Fetch region data when the component mounts
    if (mushroom.latitude && mushroom.longitude) {
      fetchRegionFromNominatim(mushroom.latitude, mushroom.longitude)
        .then(regionData => {
          setRegion(regionData || 'Unknown');
        })
        .catch(error => {
          console.error('Error fetching region from Nominatim:', error);
        });
    }
  }, [mushroom.latitude, mushroom.longitude]);
  const handleFavoriteToggle = () => {
    setIsFavorite(!isFavorite);
    const favorites = JSON.parse(localStorage.getItem('favorites')) || [];
    if (isFavorite) {
      // Remove from favorites
      const updatedFavorites = favorites.filter(id => id !== mushroom.id);
      localStorage.setItem('favorites', JSON.stringify(updatedFavorites));
    } else {
      // Add to favorites
      favorites.push(mushroom.id);
      localStorage.setItem('favorites', JSON.stringify(favorites));
    }
  };

  // Function to fetch region data from Nominatim
  async function fetchRegionFromNominatim(latitude, longitude) {
    try {
      const response = await fetch(`https://nominatim.openstreetmap.org/reverse?format=jsonv2&lat=${latitude}&lon=${longitude}`);
      const data = await response.json();
      return data.display_name || null; // Assuming the display_name is the region
    } catch (error) {
      console.error('Error fetching region data:', error);
      return null; // Return null if there's an error
    }
  }

  return (
    <li 
      className="mushroom-card" 
      onMouseEnter={() => setShowDetails(true)}
      onMouseLeave={() => setShowDetails(false)}
      onClick={() => onSelect(mushroom.id)} // Call onSelect with the mushroom ID
    >
      <img src={imageUrl} alt={mushroom.name} /> 
      <h3>{mushroom.name}</h3>
      <button onClick={handleFavoriteToggle}>
        {isFavorite ? 'Remove from Favorites' : 'Add to Favorites'}
      </button>

      {showDetails && ( 
        <div className="details-card"> 
          <p><strong>Scientific Name:</strong> {mushroom.scientific_name}</p>
          <p><strong>Region:</strong> {region}</p> {/* Display the fetched region */}
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
    }),
    latitude: PropTypes.number, // Assuming latitude and longitude are numbers
    longitude: PropTypes.number
  }).isRequired,
  onSelect: PropTypes.func.isRequired
};
export default MushroomCard;
