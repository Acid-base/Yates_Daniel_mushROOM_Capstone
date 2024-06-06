import React, { useState, useEffect, useContext, useReducer } from 'react';
import SearchBar from './SearchBar';
import ResultsList from './ResultsList';
import DetailsView from './DetailsView';
import Error from './Error';
import MushroomProvider, { MushroomContext } from './MushroomContext';
import mushroomReducer from './mushroomReducer';

function App() {
  // Context State Management 
  const [mushroomState, dispatch] = useReducer(mushroomReducer, {
    selectedMushroomId: null, 
  });

  const { mushrooms, loading, error, fetchMushroomsData } = useContext(MushroomContext);

  // Function to handle search term changes from the SearchBar
  const handleSearchChange = (newResults) => {
    // Update context state if you want to manage search results globally
    // dispatch({ type: 'UPDATE_SEARCH_RESULTS', payload: newResults }); 
  };

  // Function to handle selecting a mushroom from the results list
  const handleMushroomSelect = (mushroomId) => {
    // Update context state
    dispatch({ type: 'SELECT_MUSHROOM', payload: mushroomId }); 
  };

  // Fetch data initially on component mount
  useEffect(() => {
    fetchMushroomsData(); 
  }, []);

  return (
    <MushroomProvider> 
      <div className="app">
        <h1>Mushroom Explorer</h1>

        <SearchBar onSearchChange={handleSearchChange} />

        {error && <Error message={error} />}

        {loading && <p>Loading mushrooms...</p>}
        {!loading && (
          <>
            <ResultsList 
              mushrooms={mushrooms} 
              selectedMushroomId={mushroomState.selectedMushroomId}
              onMushroomSelect={handleMushroomSelect} 
            />

            {mushroomState.selectedMushroomId && (
              <DetailsView mushroomId={mushroomState.selectedMushroomId} />
            )}
          </>
        )}
      </div>
    </MushroomProvider> 
  );
}

export default App;