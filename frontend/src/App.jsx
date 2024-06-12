import React, { useState, useEffect, useContext } from 'react';
import { BrowserRouter, Routes, Route } from 'react-router-dom'; 
import SearchBar from './components/SearchBar';
import ResultsList from './components/ResultsList';
import DetailsView from './components/DetailsView';
import Error from './components/Error';
import MushroomProvider, { MushroomContext } from './components/MushroomContext';
import Navigation from './components/Navigation'; 

function App() {
  // Access values and functions from the MushroomContext.
  const { 
    mushrooms, 
    loading, 
    error, 
    fetchMushroomsData, 
    selectedMushroomId, 
    clearSelection 
  } = useContext(MushroomContext); 

  // Function to handle search term changes from SearchBar.
  const handleSearchChange = (searchTerm) => {
    // Update the context with the new search term (assuming MushroomContext handles this)
    // ...
  };

  // Fetch initial mushroom data when the component mounts.
  useEffect(() => {
    fetchMushroomsData(); 
  }, []); 

  return (
    <MushroomProvider>
      <BrowserRouter>
        <div className="app">
          <Navigation /> 
          <h1>Mushroom Explorer</h1>

          <SearchBar onSearchChange={handleSearchChange} /> 

          {error && <Error message={error} />}

          {loading && <p>Loading mushrooms...</p>}

          <Routes>
            <Route path="/" element={
              !loading && (
                <ResultsList 
                  mushrooms={mushrooms} 
                  onMushroomSelect={clearSelection} 
                />
              )
            } />
            <Route path="/mushroom/:id" element={
              selectedMushroomId && <DetailsView mushroomId={selectedMushroomId} />
            } />
          </Routes>

        </div>
      </BrowserRouter> 
    </MushroomProvider>
  );
}

export default App;

