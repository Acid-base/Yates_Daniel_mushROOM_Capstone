// src/components/ProfilePage.tsx
import React from "react";
import { Route } from "react-router-dom";
import PrivateRoute from "./PrivateRoute";

const ProfilePage: React.FC = () => {
  // Fetch user data and display it
  return (
    <div>
      <h1>My Profile</h1>
      {/* ... display user details */}
    </div>
  );
};

export default ProfilePage;
