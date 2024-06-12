// DetailsView.jsx 
// eslint-disable-next-line no-unused-vars
import React, { useContext } from 'react';
import { Link } from 'react-router-dom'; // Import Link for navigation
import MushroomContext from './MushroomContext'; 

function DetailsView() {
  const { selectedMushroomId, mushrooms } = useContext(MushroomContext);

  // Find the selected mushroom directly in the render method
  const selectedMushroom = mushrooms.find(
    (mushroom) => mushroom.id === selectedMushroomId
  );

  // If no mushroom is found, display a message 
  if (!selectedMushroom) {
    return <div>Select a mushroom to view details.</div>;
  }

  return (
    <div>
      {/* Back button to the home page */}
      <Link to="/">Back to Home</Link> 
      <h2>{selectedMushroom.scientificName}</h2>
      <img src={selectedMushroom.imageUrl} alt={selectedMushroom.scientificName} />
      {/* ... other details */}
    </div>
  );
}
export default DetailsView;
