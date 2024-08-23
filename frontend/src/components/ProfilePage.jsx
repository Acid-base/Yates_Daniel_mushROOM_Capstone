// src/components/ProfilePage.jsx
import React from 'react';
import { Route } from 'react-router-dom';
import PrivateRoute from './PrivateRoute';
function ProfilePage() {
  // Fetch user data and display it
  return (
    <div>
      <h1>My Profile</h1>
      {/* ... display user details */}
    </div>
  );
}

export default ProfilePage;

<Route
  path="/profile"
  element={
    <PrivateRoute>
      <ProfilePage />
    </PrivateRoute>
  }
/>;
