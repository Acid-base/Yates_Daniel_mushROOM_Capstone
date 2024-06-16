import React, { useContext } from 'react';
import { Link, NavLink, useNavigate } from 'react-router-dom';
import { MushroomContext } from './MushroomContext';
import './Navigation.css';

const Navigation: React.FC = () => {
  const { selectedMushroomId, clearSelection } = useContext(MushroomContext);
  const navigate = useNavigate();

  const handleClearSelection = () => {
    clearSelection();
    navigate('/');
  };

  return (
    <nav>
      <ul>
        <li>
          <NavLink to="/" end>
            Home
          </NavLink>
        </li>
        {selectedMushroomId && (
          <>
            <li>
              <Link to={`/mushroom/${selectedMushroomId}`}>Details</Link>
            </li>
            <li>
              <button onClick={handleClearSelection}>Clear Selection</button>
            </li>
          </>
        )}
        <li>
          <Link to="/profile">Profile</Link>
        </li>
        <li>
          <Link to="/blog">Blog</Link>
        </li>
        <li>
          <Link to="/about">About</Link>
        </li>
      </ul>
    </nav>
  );
};

export default Navigation;
