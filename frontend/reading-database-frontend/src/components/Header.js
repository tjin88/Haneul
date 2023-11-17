import React, { useState } from 'react';
import './Header.scss';
import ManBlackWhite from '../assets/ManBlackWhite.png';
import { useAuth } from './AuthContext2';
import LoginModal from './LoginModal3';
import ManColour from '../assets/ManColour.png';

const Header = () => {
  const { user, login, register, logout } = useAuth();
  // const [userInfo, setUserInfo] = useState([]);
  const [showModal, setShowModal] = useState(false);

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
      </div>

      {user 
        ? (
          <div className="top-bar">
            <button onClick={logout} className="login-button">Logout</button>
            {/* Profile Button */}
            <button className="profile-button">
              <img src={user.image || ManColour} alt="Profile" />
            </button>
          </div>
        ) : (
          <div className="top-bar">
            <button onClick={() => setShowModal(true)} className="login-button">Login</button>
            {/* ... */}
          </div>
        )
      }
      {showModal && <LoginModal onClose={() => setShowModal(false)} user={user} login={login} />}
    </header>
  );
};

export default Header;
