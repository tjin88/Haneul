import React, { useState, useEffect } from 'react';
import { useAuth } from '../components/AuthContext';
import './UserProfile.scss';

const UserProfile = ({ lightMode }) => {
  const { isLoggedIn } = useAuth();

  return (
    <div className="user-profile">
      
    </div>
  );
};

export default UserProfile;