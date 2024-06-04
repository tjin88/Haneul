import React, { useState, useEffect } from 'react';
import './CookieNotice.scss';
const CookieNotice = () => {
  const [isVisible, setIsVisible] = useState(false);

  useEffect(() => {
    const cookieAccepted = localStorage.getItem('cookieAccepted');
    if (!cookieAccepted) {
      setIsVisible(true);
    }
  }, []);

  const handleAccept = () => {
    // Set a flag in localStorage to remember that the user has accepted the cookie policy
    localStorage.setItem('cookieAccepted', 'true');
    setIsVisible(false);
  };

  if (!isVisible) return null;

  return (
    <div className="cookie-notice">
      <p>
        We use cookies to ensure you get the best experience on our website. By continuing to use our site, you accept our use of cookies and local storage. <a href="/privacy-policy">Learn more</a>.
      </p>
      <button onClick={handleAccept}>Accept</button>
    </div>
  );
};

export default CookieNotice;
