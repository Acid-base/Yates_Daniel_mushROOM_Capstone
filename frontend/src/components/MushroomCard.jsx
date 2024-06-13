import React, { useState, useEffect } from 'react';
import PropTypes from 'prop-types'; // Import PropTypes
import './MushroomCard.css'; 

function MushroomCard({ mushroom, onSelect }) {
  const [isFavorite, setIsFavorite] = useState(false);
  const [region, setRegion] = useState('Unknown'); 
  const [showDetails, setShowDetails] = useState(false); // Add state for details card visibility
  const imageUrl = mushroom.primary_image?.medium_url || 'placeholder-image.jpg';

  useEffect(() => {
    // Check if the mushroom is in the user's favorites in local storage
    const favoriteIds = getFavoritesFromLocalStorage();
    setIsFavorite(favoriteIds.includes(mushroom.id));
  }, [mushroom.id]);

  // Fetch region from Nominatim (if not already in local storage)
  useEffect(() => {
    const storedRegion = getRegionFromLocalStorage(mushroom.id);
    if (storedRegion) {
      setRegion(storedRegion);
    } else {
      fetchRegionFromNominatim(mushroom.latitude, mushroom.longitude)
        .then(regionData => {
          setRegion(regionData || 'Unknown');
          storeRegionInLocalStorage(mushroom.id, regionData);
        })
        .catch(error => {
          console.error('Error fetching region from Nominatim:', error);
        });
    }
  }, [mushroom.latitude, mushroom.longitude, mushroom.id]);

  const handleFavoriteToggle = () => {
    setIsFavorite(!isFavorite);
    updateFavoritesInLocalStorage(mushroom.id, !isFavorite); 
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

  // Function to get region from local storage
  function getRegionFromLocalStorage(mushroomId) {
    const regions = JSON.parse(localStorage.getItem('regions')) || {};
    return regions[mushroomId];
  }

  // Function to store region in local storage
  function storeRegionInLocalStorage(mushroomId, region) {
    const regions = JSON.parse(localStorage.getItem('regions')) || {};
    regions[mushroomId] = region;
    localStorage.setItem('regions', JSON.stringify(regions));
  }

  // Function to get favorites from local storage
  function getFavoritesFromLocalStorage() {
    return JSON.parse(localStorage.getItem('favorites')) || [];
  }

  // Function to update favorites in local storage
  function updateFavoritesInLocalStorage(mushroomId, isFavorite) {
    let favorites = getFavoritesFromLocalStorage();
    if (isFavorite) {
      if (!favorites.includes(mushroomId)) {
        favorites.push(mushroomId);
      }
    } else {
      favorites = favorites.filter(id => id !== mushroomId);
    }
    localStorage.setItem('favorites', JSON.stringify(favorites));
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

