import React from 'react';
import './Footer.scss';

const Footer = () => {
  return (
    <footer className="footer">
      <div className="footer-content">
        <p>&copy; {new Date().getFullYear()} TJin. All rights reserved.</p>
        {/* You can add more footer content here such as links, social media icons, etc. */}
      </div>
    </footer>
  );
};

export default Footer;
