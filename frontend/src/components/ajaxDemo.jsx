// eslint-disable-next-line no-unused-vars
import React, { useState, useEffect } from 'react';
import MushroomCard from './MushroomCard'; // Assume you have a MushroomCard component

function MushroomList() {
  const [mushrooms, setMushrooms] = useState([]); // State to store fetched mushrooms
  const [isLoading, setIsLoading] = useState(false); // State for loading indicator
  const [error, setError] = useState(null); // State for error handling

  // Fetch mushrooms data when the component mounts
  useEffect(() => {
    const fetchMushrooms = async () => {
      setIsLoading(true);
      try {
        const response = await fetch('https://api.example.com/mushrooms'); // Replace with your actual API endpoint
        if (!response.ok) {
          throw new Error('Failed to fetch mushroom data');
        }
        const data = await response.json();
        setMushrooms(data); // Update mushrooms state with fetched data
      } catch (error) {
        setError(error.message); // Update error state
      } finally {
        setIsLoading(false);
      }
    };

    fetchMushrooms();
  }, []); // Run once on component mount

  // Render the mushroom list
  return (
    <div>
      {isLoading && <p>Loading...</p>} 
      {error && <p>Error: {error}</p>}
      <ul>
        {mushrooms.map((mushroom) => (
          <MushroomCard key={mushroom.id} mushroom={mushroom} /> 
        ))}
      </ul>
    </div>
  );
}

export default MushroomList; // Export the component