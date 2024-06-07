import React, { useState, useEffect, useContext, useReducer } from 'react';
import SearchBar from './components/SearchBar';
import ResultsList from './components/ResultsList';
import DetailsView from './components/DetailsView';
import Error from './components/Error';
import MushroomProvider, { MushroomContext } from './components/MushroomContext';
import mushroomReducer from './components/mushroomReducer';

function App() {
  // Initialize state using the `useReducer` hook.
  // 'mushroomState' will hold the state managed by 'mushroomReducer'.
  // 'dispatch' is a function to update the state by dispatching actions.
  const [mushroomState, dispatch] = useReducer(mushroomReducer, {
    // Initial state: no mushroom selected by default.
    selectedMushroomId: null, 
  });

  // Access values and functions from the `MushroomContext`.
  const { mushrooms, loading, error, fetchMushroomsData } = useContext(MushroomContext);

  // State to store fetched mushrooms data.
  const [fetchedMushrooms, setFetchedMushrooms] = useState([]);
  // Function to handle search term changes from SearchBar.
  const handleSearchChange = (newResults) => {
    // Currently, this function doesn't do anything with the new results. 
    // In a real application, you might update a global search results state here.
  };

  // Function to handle mushroom selection from ResultsList.
  // It dispatches a 'SELECT_MUSHROOM' action with the selected mushroom ID.
  const handleMushroomSelect = (mushroomId) => {
    dispatch({ type: 'SELECT_MUSHROOM', payload: mushroomId }); 
  };

  // Fetch initial mushroom data when the component mounts.
  useEffect(() => {
    fetchMushroomsData(); 
  }, []);

  // Update fetchedMushrooms state when mushrooms are fetched.
  useEffect(() => {
    if (mushrooms) {
      setFetchedMushrooms(mushrooms);
    }
  }, [mushrooms]); 
  return (
    // Provide the MushroomContext to the entire app.
    <MushroomProvider> 
      <div className="app">
        {/* Title of the application. */}
        <h1>Mushroom Explorer</h1>

        {/* Search bar component. */}
        <SearchBar onSearchChange={handleSearchChange} />

        {/* Display error message if there's an error. */}
        {error && <Error message={error} />}

        {/* Display loading indicator while data is being fetched. */}
        {loading && <p>Loading mushrooms...</p>}

        {/* Render ResultsList and DetailsView if not loading. */}
        {!loading && (
          <>
            {/* Results list, passing data and handlers. */}
            <ResultsList 
              mushrooms={fetchedMushrooms} // Using fetchedMushrooms state
            />

            {/* Details view, shown when a mushroom is selected. */}
            {mushroomState.selectedMushroomId && (
              <DetailsView mushroomId={mushroomState.selectedMushroomId} />
            )}
          </>
        )}
      </div>
    {/* Closing tag for MushroomProvider. */}
    </MushroomProvider> 
  );
}

// Export the App component as the default export.
export default App;
