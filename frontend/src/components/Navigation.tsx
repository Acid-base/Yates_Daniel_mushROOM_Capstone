// src/components/Navigation.tsx
import React, { useContext } from "react";
import { Link, NavLink, useNavigate } from "react-router-dom"; // Import NavLink
import { MushroomContext } from "./MushroomContext";
import "./Navigation.css"; // Import CSS file

const Navigation: React.FC = () => {
  const { selectedMushroomId, clearSelection } = useContext(MushroomContext);
  const navigate = useNavigate();

  const handleClearSelection = () => {
    clearSelection();
    navigate("/"); // Redirect to home after clearing selection
  };

  return (
    <nav>
      <ul>
        <li>
          <NavLink to="/" end>
            Home
          </NavLink>
        </li>{" "}
        {/* Use NavLink with 'end' prop */}
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
