// src/components/DetailsView.tsx
import { useParams } from 'react-router-dom';
import { useQuery } from '@tanstack/react-query';
import { fetchMushroomDetails } from '../api'; 
import ImageGallery from 'react-image-gallery';
import { Link } from 'react-router-dom';

// Assuming you have a Mushroom type
interface Mushroom {
  scientificName: string;
  images: { url: string; thumbnail_url: string }[];
  // ... other properties
}

const DetailsView = () => {
  const { id } = useParams();
  const mushroomId = parseInt(id!, 10); 

  const { isLoading, error, data: mushroom } = useQuery<Mushroom, Error>(
    ['mushroom', mushroomId], 
    () => fetchMushroomDetails(mushroomId)
  );

  if (isLoading) return <p>Loading details...</p>;
  if (error) return <p>Error: {error.message}</p>;
  if (!mushroom) return <p>Mushroom not found.</p>;

  // ... render details using the 'mushroom' data

  return (
    // ... JSX to render details using mushroom data
  );
};
export default DetailsView;
