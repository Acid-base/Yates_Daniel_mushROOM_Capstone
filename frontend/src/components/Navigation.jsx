// src/components/Navigation.jsx
import React, { useContext } from 'react';
import { Link, useNavigate } from 'react-router-dom';
import { MushroomContext } from './MushroomContext';

function Navigation() {
  const { selectedMushroomId, clearSelection } = useContext(MushroomContext);
  const navigate = useNavigate();

  const handleClearSelection = () => {
    clearSelection();
    navigate('/'); // Redirect to home after clearing selection
  };

  return (
    <nav>
      <Link to="/">Home</Link>
      {selectedMushroomId && (
        <>
          <Link to={`/mushroom/${selectedMushroomId}`}>Details</Link>
          <button onClick={handleClearSelection}>Clear Selection</button>
        </>
      )}
      <Link to="/profile">Profile</Link>
      <Link to="/blog">Blog</Link>
      <Link to="/about">About</Link>
    </nav>
  );
}

export default Navigation;
