import React from 'react';
import './Footer.scss';

const Footer = () => {
  return (
    <footer className="footer">
      <div className="footer-content">
        <p>&copy; {new Date().getFullYear()} TJin. All rights reserved. Please email tjin368@gmail.com for any comments or inquiries.</p>
      </div>
    </footer>
  );
};

export default Footer;
