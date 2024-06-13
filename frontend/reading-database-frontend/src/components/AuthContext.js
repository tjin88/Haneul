import React, { createContext, useContext, useState, useEffect } from 'react';
// import { useCsrf } from './CsrfContext';

const AuthContext = createContext();

export const useAuth = () => useContext(AuthContext);

export const AuthProvider = ({ children }) => {
  const [user, setUser] = useState(null);
  const [isLoggedIn, setIsLoggedIn] = useState(false);
  // const { csrfToken, getCsrfToken } = useCsrf();

  const parseJwt = (token) => {
    var base64Url = token.split('.')[1];
    var base64 = base64Url.replace(/-/g, '+').replace(/_/g, '/');
    var jsonPayload = decodeURIComponent(window.atob(base64).split('').map(function(c) {
        return '%' + ('00' + c.charCodeAt(0).toString(16)).slice(-2);
    }).join(''));

    return JSON.parse(jsonPayload);
  }

  // Check local storage for user data on initial load
  useEffect(() => {
    // Function to load user data from localStorage
    const loadUserFromLocalStorage = () => {
      const storedToken = localStorage.getItem('token');
      if (storedToken) {
        const decodedToken = parseJwt(storedToken);
        const user = {
          username: decodedToken.username,
          profileName: decodedToken.profileName,
          profileImage: decodedToken.profileImage,
          darkMode: decodedToken.darkMode,
          emailNotifications: decodedToken.emailNotifications,
        };
        
        setIsLoggedIn(true);
        setUser(user);
      }
    };

    // getCsrfToken();
    loadUserFromLocalStorage();
  }, []);

  const login = async (email, password) => {
    try {
      // await getCsrfToken();
      const response = await fetch(`${process.env.REACT_APP_API_URL}/centralized_API_backend/api/login/`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          // 'X-CSRFToken': csrfToken,
        },
        credentials: 'include',
        body: JSON.stringify({ email, password }),
      });
  
      if (!response.ok) {
        throw new Error('Login failed');
      }
  
      const data = await response.json();
      const decodedToken = parseJwt(data.token);
      const user = {
        username: decodedToken.username,
        profileName: decodedToken.profileName,
        profileImage: decodedToken.profileImage,
        darkMode: decodedToken.darkMode,
        emailNotifications: decodedToken.emailNotifications,
      };
  
      setUser(user);
      setIsLoggedIn(true);
      localStorage.setItem('token', data.token);
    } catch (err) {
      console.error('Login error:', err);
      throw err;
    }
  };

  const register = async (email, password, profileName ) => {
    try {
      // await getCsrfToken();
      const response = await fetch(`${process.env.REACT_APP_API_URL}/centralized_API_backend/api/register/`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          // 'X-CSRFToken': csrfToken,
        },
        credentials: 'include',
        body: JSON.stringify({ email, password, profileName }),
      });
  
      const data = await response.json();

      if (!response.ok) {
        if (data.error) {
            throw new Error(data.error);
        } else {
            throw new Error('Registration failed');
        }
      }

      const decodedToken = parseJwt(data.token);
      const user = {
        username: decodedToken.username,
        profileName: decodedToken.profileName
      };

      setUser(user);
      setIsLoggedIn(true);
      localStorage.setItem('token', data.token);
    } catch (err) {
      console.error('Registration error:', err);
      throw err;
    }
  };

  const logout = () => {
    setUser(null);
    setIsLoggedIn(false);
    localStorage.removeItem('token');
    console.log('Logged out!')
    window.location.href = window.location.origin;
  };

  const deleteUserAccount = async () => {
    try {
      // await getCsrfToken();
      const response = await fetch(`${process.env.REACT_APP_API_URL}/centralized_API_backend/api/delete_user/`, {
        method: 'DELETE',
        headers: {
          'Content-Type': 'application/json',
          // 'X-CSRFToken': csrfToken,
        },
        credentials: 'include',
        body: JSON.stringify({ email: user.username }),
      });

      if (!response.ok) {
        throw new Error('Delete account failed');
      }

      setUser(null);
      setIsLoggedIn(false);
      localStorage.removeItem('token');
      console.log('Account deleted!')
      window.location.href = window.location.origin;
    } catch (err) {
      console.error('Delete account error:', err);
      throw err;
    }
  };
  
  const updateUserProfile = async (profileData) => {
    try {
      const token = localStorage.getItem('token');
      // await getCsrfToken();
      const response = await fetch(`${process.env.REACT_APP_API_URL}/centralized_API_backend/api/update_user_profile/`, {
        method: 'PUT',
        headers: {
          'Authorization': `Bearer ${token}`,
          // 'X-CSRFToken': csrfToken,
          'Content-Type': 'application/json',
        },
        credentials: 'include',
        body: JSON.stringify(profileData),
      });
  
      if (!response.ok) {
        throw new Error('Profile update failed');
      }
  
      const data = await response.json();
      const updatedUser = {
        ...user,
        profileImage: data.profileImage,
      };
      setUser(updatedUser);
    } catch (err) {
      console.error('Profile update error:', err);
      throw err;
    }
  };  

  const value = { 
    isLoggedIn,
    user, 
    login, 
    register, 
    logout,
    deleteUserAccount,
    updateUserProfile,
  };

  return <AuthContext.Provider value={value}>{children}</AuthContext.Provider>;
};