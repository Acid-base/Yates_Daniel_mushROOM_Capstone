// src/components/Navigation.jsx
import React, { useContext } from 'react';
import { Link, useNavigate } from 'react-router-dom';
import { MushroomContext } from './MushroomContext';
import './Navigation.css'; // Import CSS file

function Navigation() {
  const { selectedMushroomId, clearSelection } = useContext(MushroomContext);
  const navigate = useNavigate();

  const handleClearSelection = () => {
    clearSelection();
    navigate('/'); // Redirect to home after clearing selection
  };

  return (
    <nav>
      <ul> 
        <li><Link to="/">Home</Link></li>
        {selectedMushroomId && (
          <>
            <li><Link to={`/mushroom/${selectedMushroomId}`}>Details</Link></li>
            <li><button onClick={handleClearSelection}>Clear Selection</button></li>
          </>
        )}
        <li><Link to="/profile">Profile</Link></li>
        <li><Link to="/blog">Blog</Link></li>
        <li><Link to="/about">About</Link></li>
      </ul>
    </nav>
  );
}

export default Navigation;
