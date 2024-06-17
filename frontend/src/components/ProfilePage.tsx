// src/components/ProfilePage.tsx
import React from 'react';
import { useQuery } from '@tanstack/react-query';
import { fetchUserProfile } from '../api';
const ProfilePage: React.FC = () => {
  const { isLoading, error, data: user } = useQuery('userProfile', fetchUserProfile);

  if (isLoading) return <p>Loading...</p>;
  if (error) return <p>Error: {error.message}</p>;
  return (
    <div>
      <h1>My Profile</h1>
      <p>Name: {user.name}</p>
      <p>Email: {user.email}</p>
      <p>Location: {user.location}</p>
      <p>Bio: {user.bio}</p>
      {/* Display other user details */}
    </div>
  );
};

export default ProfilePage;
