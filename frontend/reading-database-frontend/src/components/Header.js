import React, { useState, useEffect } from 'react';
import './Header.scss';
import ManBlackWhite from '../assets/ManBlackWhite.png';
import { useAuth } from './AuthContext';
import LoginModal from './LoginModal';
import ManColour from '../assets/ManColour.png';
import Sun from '../assets/Sun.png';
import Moon from '../assets/Moon.png';

const Header = ({ isLightMode, setLightMode }) => {
  const { user, login, logout } = useAuth();
  const [showModal, setShowModal] = useState(false);
  const [isLoggingIn, setIsLoggingIn] = useState(false);
  const [profileName, setProfileName] = useState("");

  const loadUserFromLocalStorage = () => {
    const storedUser = localStorage.getItem('user');
    if (storedUser) {
      setProfileName(JSON.parse(storedUser).profileName);
    }
  };

  // Check local storage for user data on initial load
  useEffect(() => {
    loadUserFromLocalStorage();
  }, []);

  return (
    <header className="header">
      <div className="left-side">
        <a href="/" className="branding">
          <img src={ManBlackWhite} alt="Logo" className="logo" />
          <h1 className="title">Manga and Light Novel Tracker</h1>
        </a>

        <a href="/browse" className="header_browse_redirect">
          <h1 className="browse_redirect">Browse</h1>
        </a>

        <a href="/track" className="header_browse_redirect">
          <h1 className="browse_redirect">Track</h1>
        </a>
      </div>

      <div className="top-bar">
        {user 
          ? (
            <>
              <button onClick={logout} className="login-button">Logout</button>
              {/* Profile Button */}
              <button className="profile-button">
                {/* <p>{profileName}</p> */}
                <img src={user.image || ManColour} alt="Profile" />
              </button>
              </>
          ) : (
            <>
              <button onClick={() => {setShowModal(true); setIsLoggingIn(false)}} className="login-button">Register</button>
              <button onClick={() => {setShowModal(true); setIsLoggingIn(true)}} className="login-button">Login</button>
            </>
          )
        }
        {isLightMode 
          ? <img className="sunMoon" src={Moon} alt="Moon" onClick={() => setLightMode(!isLightMode)} />
          : <img className="sunMoon" src={Sun} alt="Sun" onClick={() => setLightMode(!isLightMode)} />
        }
      </div>
      {showModal && <LoginModal onClose={() => setShowModal(false)} user={user} login={login} isLoggingIn={isLoggingIn} />}
    </header>
  );
};

export default Header;
