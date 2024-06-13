import React, { createContext, useContext, useState, useEffect } from 'react';

const CsrfContext = createContext();

export const useCsrf = () => useContext(CsrfContext);

export const CsrfProvider = ({ children }) => {
  const [csrfToken, setCsrfToken] = useState('');

  const getCsrfToken = async () => {
    try {
      const response = await fetch(`${process.env.REACT_APP_API_URL}/centralized_API_backend/api/csrf-token/`, {
        method: 'GET',
        credentials: 'include',
      });
      const data = await response.json();
      setCsrfToken(data.csrfToken);
      return data.csrfToken;
    } catch (err) {
      console.error('Failed to fetch CSRF token', err);
    }
  };

  useEffect(() => {
    getCsrfToken();
  }, []);

  return (
    <CsrfContext.Provider value={{ csrfToken, getCsrfToken }}>
      {children}
    </CsrfContext.Provider>
  );
};