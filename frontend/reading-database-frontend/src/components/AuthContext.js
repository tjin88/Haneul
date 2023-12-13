import React, { createContext, useContext, useState, useEffect } from 'react';
// import jwtDecode from 'jwt-decode';

const AuthContext = createContext();

export const useAuth = () => useContext(AuthContext);

export const AuthProvider = ({ children }) => {
  const [user, setUser] = useState(null);
  const [isLoggedIn, setIsLoggedIn] = useState(false);

  const API_ENDPOINT = 'http://127.0.0.1:8000';

  const parseJwt = (token) => {
    var base64Url = token.split('.')[1];
    var base64 = base64Url.replace(/-/g, '+').replace(/_/g, '/');
    var jsonPayload = decodeURIComponent(window.atob(base64).split('').map(function(c) {
        return '%' + ('00' + c.charCodeAt(0).toString(16)).slice(-2);
    }).join(''));

    return JSON.parse(jsonPayload);
  }

  // Function to load user data from localStorage
  const loadUserFromLocalStorage = () => {
    const storedToken = localStorage.getItem('token');
    if (storedToken) {
      const decodedToken = parseJwt(storedToken);
      const user = {
        username: decodedToken.username,
        profileName: decodedToken.profileName
      };
  
      setUser(user);
    }
  };

  // Check local storage for user data on initial load
  useEffect(() => {
    loadUserFromLocalStorage();
  }, []);

  const login = async (email, password) => {
    try {
      const response = await fetch(`${API_ENDPOINT}/centralized_API_backend/api/login/`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({ email, password }),
      });
  
      if (!response.ok) {
        throw new Error('Login failed');
      }
  
      const data = await response.json();
      const decodedToken = parseJwt(data.token);
      const user = {
        username: decodedToken.username,
        profileName: decodedToken.profileName
      };
  
      setUser(user);
      localStorage.setItem('token', data.token);
    } catch (err) {
      console.error('Login error:', err);
      throw err;
    }
  };

  const register = async (email, password, profileName ) => {
    try {
      const response = await fetch(`${API_ENDPOINT}/centralized_API_backend/api/register/`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
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
      localStorage.setItem('token', data.token);
    } catch (err) {
      console.error('Registration error:', err);
      throw err;
    }
  };
  

  const logout = () => {
    setUser(null);
    localStorage.removeItem('token');
  };

  const value = { 
    isLoggedIn,
    user, 
    login, 
    register, 
    logout 
  };

  return <AuthContext.Provider value={value}>{children}</AuthContext.Provider>;
};
