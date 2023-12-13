import React, { createContext, useContext, useState, useEffect } from 'react';

const AuthContext = createContext();

export const useAuth = () => useContext(AuthContext);

export const AuthProvider = ({ children }) => {
  const [user, setUser] = useState(null);

  const API_ENDPOINT = 'http://127.0.0.1:8000';

  // Function to load user data from localStorage
  const loadUserFromLocalStorage = () => {
    const storedUser = localStorage.getItem('user');
    if (storedUser) {
      setUser(JSON.parse(storedUser));
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
      setUser({ ...data.user });
      localStorage.setItem('user', JSON.stringify(data.user));
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

      setUser({ ...data.user });
      localStorage.setItem('user', JSON.stringify(data.user));
    } catch (err) {
      console.error('Registration error:', err);
      throw err;
    }
  };
  

  const logout = () => {
    setUser(null);
    localStorage.removeItem('user');
  };

  const value = { 
    user, 
    login, 
    register, 
    logout 
  };

  return <AuthContext.Provider value={value}>{children}</AuthContext.Provider>;
};
