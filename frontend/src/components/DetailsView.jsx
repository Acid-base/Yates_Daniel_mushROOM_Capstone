// DetailsView.jsx 
// Import React and useContext for using React Context API.
import React, { useContext } from 'react';
// Import the MushroomContext to access shared data.
import MushroomContext from './MushroomContext'; // Import the named export 

// Define the DetailsView functional component.
function DetailsView() {
  // Get the 'selectedMushroomId' from the MushroomContext using useContext.
  const { selectedMushroomId, mushrooms } = useContext(MushroomContext); // Access selectedMushroomId from the context

  // Retrieve the selected mushroom from 'mushrooms' based on 'selectedMushroomId'.
  // If 'selectedMushroomId' is null (no selection), 'selectedMushroom' will be null.
  const selectedMushroom = selectedMushroomId ? mushrooms.find((mushroom) => mushroom.id === selectedMushroomId) : null; 

  // If no mushroom is selected ('selectedMushroom' is null), render a message.
  if (!selectedMushroom) {
    return <div>Select a mushroom to view details.</div>;
  }

  // ... (render details of the 'selectedMushroom' here)
}

// Export the DetailsView component as the default export.
export default DetailsView;


