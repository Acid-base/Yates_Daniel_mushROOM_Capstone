import React, { useContext, useEffect } from 'react';
import { BrowserRouter as Router, Route, Routes } from 'react-router-dom';
import Error from './components/Error';
import MushroomProvider, {
  MushroomContext,
} from './components/MushroomContext';
import ProfilePage from './components/ProfilePage';
import PrivateRoute from './components/PrivateRoute';

const App = () => {
  const { clearSelection, selectedMushroomId, isAuthenticated } =
    useContext(MushroomContext);
  useEffect(() => {
    if (selectedMushroomId) {
      navigate(`/mushrooms/${selectedMushroomId}`);
      clearSelection();
    }
  }, [selectedMushroomId, navigate, clearSelection]); // Remove location dependency
  return (
    <Router>
      <div>
        <h1>Mushroom App</h1>
        <Routes>
          <Route
            path="/"
            element={
              <PrivateRoute>
                <ProfilePage />
              </PrivateRoute>
            }
          />
          <Route
            path="/error"
            element={<Error message="An error occurred." />}
          />
          {/* Add other routes here */}
        </Routes>
      </div>
    </Router>
  );
};

App.displayName = 'App';
export default App;
