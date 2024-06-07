import React, { useState, useEffect } from 'react';

function MushroomList() {
  const [mushrooms, setMushrooms] = useState([]);
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState(null);

  useEffect(() => {
    const fetchMushrooms = async () => {
      setIsLoading(true);
      try {
        const response = await fetch('https://api.example.com/mushrooms'); // Replace with actual API endpoint 
        if (!response.ok) {
          throw new Error('Failed to fetch mushroom data');
        }
        const data = await response.json();
        setMushrooms(data); 
      } catch (error) {
        setError(error.message);
      } finally {
        setIsLoading(false);
      }
    };

    fetchMushrooms();
  }, []); // Empty dependency array ensures this runs once on mount

  // ... Rest of your component logic to display the mushrooms 
}
