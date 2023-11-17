import React from 'react';
import './NotFound.scss';

const NotFound = ({ lightMode }) => {
  return (
    <div className="not-found-container">
      <h1>404</h1>
      <p>The page you're looking for cannot be found.</p>
    </div>
  );
};

export default NotFound;
