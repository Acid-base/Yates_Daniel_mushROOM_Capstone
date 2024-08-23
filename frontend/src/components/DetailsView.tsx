// src/components/DetailsView.tsx
import { useParams } from 'react-router-dom';
import { useQuery } from '@tanstack/react-query';
import { fetchMushroomDetails } from '../api';
import ImageGallery from 'react-image-gallery';
import { Link } from 'react-router-dom';

interface Mushroom {
  scientificName: string;
  images: { url: string; thumbnail_url: string }[];
  // ... other properties
}

const DetailsView: React.FC = () => {
  const { id } = useParams();
  const mushroomId = parseInt(id!, 10);

  const {
    isLoading,
    error,
    data: mushroom,
  } = useQuery<Mushroom, Error>(['mushroom', mushroomId], () =>
    fetchMushroomDetails(mushroomId)
  );

  if (isLoading) return <p>Loading details...</p>;
  if (error) return <p>Error: {error.message}</p>;
  if (!mushroom) return <p>Mushroom not found.</p>;

  return (
    <div>
      <h1>{mushroom.scientificName}</h1>
      <ImageGallery
        items={mushroom.images.map(image => ({
          original: image.url,
          thumbnail: image.thumbnail_url,
        }))}
      />
      {/* Render other mushroom details */}
    </div>
  );
};
export default DetailsView;
