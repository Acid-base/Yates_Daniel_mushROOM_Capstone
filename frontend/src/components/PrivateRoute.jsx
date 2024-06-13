// src/components/PrivateRoute.jsx
import { Navigate, Outlet, useLocation } from 'react-router-dom';
import { useContext } from 'react';
import { MushroomContext } from './MushroomContext';

function PrivateRoute() {
  const { isAuthenticated } = useContext(MushroomContext); // Access authentication state
  const location = useLocation();

  return isAuthenticated ? <Outlet /> : <Navigate to="/login" state={{ from: location }} replace />;
}

export default PrivateRoute;

