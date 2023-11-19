import React, { createContext, useContext, useState, useEffect } from 'react';

const AuthContext = createContext();

export const useAuth = () => useContext(AuthContext);

export const AuthProvider = ({ children }) => {
  const [user, setUser] = useState(null);

  /*
  // TODO: Add tokenization for authenticating users**
  function getCookie(name) {
    let cookieValue = null;
    if (document.cookie && document.cookie !== '') {
        const cookies = document.cookie.split(';');
        for (let i = 0; i < cookies.length; i++) {
            const cookie = cookies[i].trim();
            if (cookie.substring(0, name.length + 1) === (name + '=')) {
                cookieValue = decodeURIComponent(cookie.substring(name.length + 1));
                break;
            }
        }
    }
    return cookieValue;
  }

  const csrftoken = getCookie('csrftoken');
  */

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
      const response = await fetch('http://127.0.0.1:8000/centralized_API_backend/api/login/', {
        method: 'POST',
        headers: {
        //   'X-CSRFToken': csrftoken,
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
      const response = await fetch('http://127.0.0.1:8000/centralized_API_backend/api/register/', {
        method: 'POST',
        headers: {
        //   'X-CSRFToken': csrftoken, // Replace with your CSRF token
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
    // localStorage.removeItem('token');
  };
  

  return (
    <AuthContext.Provider value={{ user, login, register, logout }}>
      {children}
    </AuthContext.Provider>
  );
};
