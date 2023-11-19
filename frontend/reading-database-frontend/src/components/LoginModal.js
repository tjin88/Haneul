import React, { useState } from 'react';
import { useAuth } from './AuthContext';
import './LoginModal.scss';

const LoginModal = ({ onClose }) => {
  const { login, register } = useAuth();
  const [isLogin, setIsLogin] = useState(true);
  const [email, setEmail] = useState('');
  const [passwordVisible, setPasswordVisible] = useState(false);
  const [password, setPassword] = useState('');
  const [profileName, setProfileName] = useState('');
  const [error, setError] = useState('');

  const validatePassword = (password) => {
    const regex = /^(?=.*[A-Z])(?=.*[!@#$&*])(?=.*[0-9]).{8,}$/;
    return regex.test(password);
  };

  const validateProfileName = (name) => {
    // Ensure profile name does not exceed 12 characters
    return name.length <= 12; 
  };

  const togglePasswordVisibility = () => {
    setPasswordVisible(!passwordVisible);
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    setError('');
  
    if (!isLogin) {
      if (!validatePassword(password)) {
        setError('Invalid password. Ensure it has:\n- At least 8 characters\n- At least one uppercase letter\n- At least one special character\n- At least one number');
        return;
      }
      if (!validateProfileName(profileName)) {
        setError('Profile name should not exceed 12 characters.');
        return;
      }
      try {
        await register(email, password, profileName);
        onClose();
      } catch (err) {
        setError(err.message);
      }
    } else {
      try {
        await login(email, password);
        onClose();
      } catch (err) {
        setError(err.message);
      }
    }
  };

  return (
    <div className="overlay">
        <div className="modal">
            <form onSubmit={handleSubmit}>
                <input
                  type="email"
                  value={email}
                  onChange={(e) => setEmail(e.target.value)}
                  placeholder="Email"
                  required
                />
                <div className="password-input-container">
                    <input
                      type={passwordVisible ? "text" : "password"}
                      value={password}
                      onChange={(e) => setPassword(e.target.value)}
                      placeholder="Password"
                      required
                    />
                    <button 
                      type="button" 
                      onClick={togglePasswordVisibility}
                      className="toggle-password-visibility"
                    >
                      {passwordVisible ? '🔒' : '🔓'}
                    </button>
                </div>
                {!isLogin && (
                  <input
                    type="text"
                    value={profileName}
                    onChange={(e) => setProfileName(e.target.value)}
                    placeholder="Profile Name (max 12 chars)"
                    maxLength="12"
                  />
                )}
                {error && <pre className="error">{error}</pre>}
                <button type="submit">{isLogin ? 'Login' : 'Register'}</button>
            </form>
            <div className="login_register_close_button">
                <button onClick={() => setIsLogin(!isLogin)}>
                    {isLogin ? 'Need an account? Register' : 'Already have an account? Login'}
                </button>
                <button onClick={onClose}>Close</button>
            </div>
        </div>
      </div>
  );
};

export default LoginModal;
