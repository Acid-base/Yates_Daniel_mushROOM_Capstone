import React, { useContext } from 'react';
import MushroomContext from '../MushroomContext'; // Import the named export 

function DetailsView() {
  const { selectedMushroomId } = useContext(MushroomContext); // Access selectedMushroomId from the context

  // Check if searchResults is available and find the selected mushroom
  const selectedMushroom = selectedMushroomId ? mushrooms.find((mushroom) => mushroom.id === selectedMushroomId) : null; 

  if (!selectedMushroom) {
    return <div>Select a mushroom to view details.</div>;
  }

  // ... (render details)
}

export default DetailsView;

