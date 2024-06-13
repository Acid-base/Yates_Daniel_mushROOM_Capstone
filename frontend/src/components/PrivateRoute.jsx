// src/components/PrivateRoute.jsx
import { Navigate, Outlet, useLocation } from 'react-router-dom';

function PrivateRoute({ isAuthenticated, children }) { // Receive isAuthenticated prop
  const location = useLocation();

  return isAuthenticated ? ( // Check authentication status
    children 
  ) : (
    <Navigate to="/login" state={{ from: location }} replace />
  );
}

export default PrivateRoute;
