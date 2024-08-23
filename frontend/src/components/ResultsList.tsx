// ResultsList.tsx
import React from 'react';
import { useQuery } from '@tanstack/react-query';
import { fetchMushrooms } from '../api';
import MushroomCard from './MushroomCard';

const MushroomList: React.FC = () => {
  const {
    isLoading,
    error,
    data: mushrooms,
  } = useQuery('mushrooms', () => fetchMushrooms());
  if (isLoading) return <p>Loading...</p>;
  if (error) return <p>Error: {error.message}</p>;

  return (
    <div>
      <h1>Mushrooms</h1>
      {mushrooms.map(mushroom => (
        <MushroomCard key={mushroom.id} mushroom={mushroom} />
      ))}
    </div>
  );
};

export default MushroomList;
