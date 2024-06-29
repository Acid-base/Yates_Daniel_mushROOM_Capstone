// src/components/MushroomCard.tsx
import React, { useState } from 'react';
import PropTypes from 'prop-types';
import './MushroomCard.css';
import axios from 'axios';
import { useMutation, useQueryClient } from '@tanstack/react-query';

interface MushroomCardProps {
  mushroom: any;
  onSelect: (mushroomId: string) => void;
}

const MushroomCard: React.FC<MushroomCardProps> = ({ mushroom, onSelect }) => {
  const [isFavorite, setIsFavorite] = useState(false);
  const [showDetails, setShowDetails] = useState(false);
  const queryClient = useQueryClient();

  // Function to get token from local storage
  const getToken = () => {
    return localStorage.getItem('token');
  };

  const toggleFavoriteMutation = useMutation(
    async () => {
      const token = getToken();
      if (!token) {
        throw new Error('User not authenticated!');
      }

      const response = await axios.post(
        `/mushrooms/${mushroom.id}/favorites`,
        {},
        {
          headers: {
            Authorization: `Bearer ${token}`,
          },
        }
      );
      return response.data;
    },
    {
      onSuccess: () => {
        // Invalidate the 'mushrooms' query to trigger a refetch
        queryClient.invalidateQueries(['mushrooms']);
        updateFavorites(mushroom.id);
      },
      onError: error => {
        console.error('Error toggling favorite:', error);
        // Handle errors (e.g., display an error message)
      },
    }
  );

  // ... (rest of the component code) ...

  const handleToggleFavorite = async () => {
    try {
      await toggleFavoriteMutation.mutateAsync();
    } catch (error) {
      // Handle authentication errors (e.g., redirect to login)
      if (error.message === 'User not authenticated!') {
        // Redirect or show a message
      }
    }
  };

  return (
    <div>
      <ul>
        <li
          className="mushroom-card"
          onMouseEnter={() => setShowDetails(true)}
          onMouseLeave={() => setShowDetails(false)}
        >
          {/* ... (other content) ... */}
          <button
            onClick={handleToggleFavorite}
            disabled={toggleFavoriteMutation.isLoading}
          >
            {toggleFavoriteMutation.isLoading
              ? 'Updating...'
              : isFavorite
                ? 'Remove from Favorites'
                : 'Add to Favorites'}
          </button>
        </li>
        {/* Other list items */}
      </ul>
    </div>
  );
};

export default MushroomCard;
