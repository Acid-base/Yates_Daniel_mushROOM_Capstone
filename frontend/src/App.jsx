import React, { useState, useEffect, useContext } from 'react';
import { BrowserRouter, Routes, Route, useNavigate, useLocation } from 'react-router-dom';
import Navigation from './components/Navigation';
import SearchBar from './components/SearchBar';
import ResultsList from './components/ResultsList';
import DetailsView from './components/DetailsView';
import Error from './components/Error';
import MushroomProvider, { MushroomContext } from './components/MushroomContext';
import { fetchMushrooms } from './api'; // Import fetchMushrooms 
import ProfilePage from './components/ProfilePage'; // Import ProfilePage
import AboutPage from './components/AboutPage'; // Import AboutPage
import BlogPage from './components/BlogPage'; // Import BlogPage using 'default'
import PrivateRoute from './components/PrivateRoute'; // Import PrivateRoute

function App() {
  const {
    mushrooms,
    loading,
    error,
    selectedMushroomId,
    setSearchTerm,
    setCurrentPage,
    clearSelection,
    fetchMushrooms, // Now accessible from the context
    isAuthenticated // Add isAuthenticated from the context 
  } = useContext(MushroomContext); 
  const navigate = useNavigate(); 
  const location = useLocation();

  // Function to handle search term changes from SearchBar.
  const handleSearchChange = (searchTerm) => {
    setSearchTerm(searchTerm); 
    setCurrentPage(1); 
    fetchMushrooms(searchTerm, 1); 
  };

  // Fetch initial mushroom data when the component mounts.
  useEffect(() => {
    fetchMushrooms(); 
  }, []); 

  // Handle navigation to details view or clearing selection
  useEffect(() => {
    if (selectedMushroomId) {
      navigate(`/mushroom/${selectedMushroomId}`);
    } else if (location.pathname.startsWith('/mushroom')) {
      clearSelection();
    }
  }, [selectedMushroomId, navigate, location.pathname]);

  // Render the application UI
  return (
    <div>
      <Navigation /> 
      <h1>Mushroom Explorer</h1>

      <SearchBar onSearchChange={handleSearchChange} /> 

      {/* Display error or loading messages */}
      {error && <Error message={error} />}
      {loading && <p>Loading mushrooms...</p>}

      {/* Render routes only when data is loaded and there are mushrooms */}
      {!loading && mushrooms.length > 0 && (
        <Routes>
          <Route
            path="/"
            element={
              <ResultsList 
                mushrooms={mushrooms} 
                onMushroomSelect={clearSelection} 
              />
            }
          />
          <Route path="/mushroom/:id" element={<DetailsView />} />
          <Route path="/profile" element={<PrivateRoute><ProfilePage /></PrivateRoute>} /> {/* Add the ProfilePage route with PrivateRoute */}
          <Route path="/blog" element={<BlogPage />} /> {/* Add the BlogPage route */}
          <Route path="/about" element={<AboutPage />} /> {/* Add the AboutPage route */}
        </Routes>
      )}

    </div>
  );
}

export default () => ( 
  <MushroomProvider>
    <BrowserRouter>
      <App />
    </BrowserRouter>
  </MushroomProvider>
);
