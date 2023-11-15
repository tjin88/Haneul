import React from 'react';
import './Header.scss';
import ManBlackWhite from '../assets/ManBlackWhite.png';

const Header = ({ login, setLogin, onRegister }) => {
  return (
    <header className="header">
      <a href="/" className="branding">
        <img src={ManBlackWhite} alt="Logo" className="logo" />
        <h1 className="title">Manga and Light Novel Tracker</h1>
      </a>

      <a href="/browse" className="header_browse_redirect">
        <h1 className="browse_redirect">Browse</h1>
      </a>

      {login 
      ? <div className="top-bar">
          <button onClick={setLogin} className="login-button">Logout</button>
        </div>
      : <div className="top-bar">
          <button onClick={setLogin} className="login-button">Login</button>
          <button onClick={onRegister} className="register-button">Register</button>
        </div>
      }
    </header>
  );
};

export default Header;
