import React from 'react';
import './Footer.scss';

const Footer = () => {
  return (
    <footer className="footer">
      <div className="footer-content">
        <p>
          &copy; {new Date().getFullYear()} TJin. All rights reserved. 
          Please email tjin368@gmail.com for any comments or inquiries.
          <a className="privacy-policy" href="/privacy-policy">Privacy Policy</a>
        </p>
      </div>
    </footer>
  );
};

export default Footer;
