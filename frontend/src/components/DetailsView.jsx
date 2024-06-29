// src/components/DetailsView.jsx
import React, { useContext } from 'react';
import { Link } from 'react-router-dom';
import ImageGallery from 'react-image-gallery'; // Import ImageGallery
import MushroomContext from './MushroomContext';

function DetailsView() {
  const { selectedMushroomId, mushrooms } = useContext(MushroomContext);

  // Find the selected mushroom
  const selectedMushroom = mushrooms.find(
    mushroom => mushroom.id === selectedMushroomId
  );

  // If no mushroom is found, display a message
  if (!selectedMushroom) {
    return <div>Select a mushroom to view details.</div>;
  }

  // Prepare images for the image gallery
  const images = selectedMushroom.images.map(image => ({
    original: image.url,
    thumbnail: image.thumbnail_url,
  }));
  return (
    <div>
      {/* Back button to the home page */}
      <Link to="/">Back to Home</Link>
      <h2>{selectedMushroom.scientificName}</h2>
      {/* Image Gallery */}
      <ImageGallery items={images} />
      {/* ... other details */}
      <div>
        <h3>Habitat</h3>
        <p>{selectedMushroom.habitat}</p>
      </div>
      {/* ... more detail cards */}
    </div>
  );
}
export default DetailsView;
