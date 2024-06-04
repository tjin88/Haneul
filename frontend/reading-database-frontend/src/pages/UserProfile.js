import React, { useState, useEffect } from 'react';
import { useAuth } from '../components/AuthContext';
import './UserProfile.scss';

const UserProfile = ({ lightMode, setLightMode }) => {
  const { isLoggedIn, user, updateUserProfile, changeUserPassword, deleteUserAccount } = useAuth();
  const [editingProfile, setEditingProfile] = useState(false);
  const [changingPassword, setChangingPassword] = useState(false);
  const [emailNotifications, setEmailNotifications] = useState(user ? user.emailNotifications : false);
  const [pushNotifications, setPushNotifications] = useState(user ? user.pushNotifications : false);
  const [language, setLanguage] = useState(user ? user.language : 'en');

  const [profileData, setProfileData] = useState({
    name: '',
    email: '',
    profilePicture: ''
  });

  const [passwordData, setPasswordData] = useState({
    currentPassword: '',
    newPassword: '',
    confirmPassword: ''
  });

  const [importList, setImportList] = useState(null);

  useEffect(() => {
    if (user) {
      setProfileData({
        name: user.name,
        email: user.email,
        profilePicture: user.profilePicture
      });
      setEmailNotifications(user.emailNotifications);
      setPushNotifications(user.pushNotifications);
      setLanguage(user.language);
    }
  }, [user]);

  const handleProfileChange = (e) => {
    setProfileData({ ...profileData, [e.target.name]: e.target.value });
  };

  const handlePasswordChange = (e) => {
    setPasswordData({ ...passwordData, [e.target.name]: e.target.value });
  };

  const handleProfileSubmit = (e) => {
    e.preventDefault();
    updateUserProfile(profileData, emailNotifications, pushNotifications, language);
    setEditingProfile(false);
  };

  const handlePasswordSubmit = (e) => {
    e.preventDefault();
    if (passwordData.newPassword === passwordData.confirmPassword) {
      changeUserPassword(passwordData.currentPassword, passwordData.newPassword);
      setChangingPassword(false);
    } else {
      alert('New password and confirm password do not match');
    }
  };

  const handleImportList = (e) => {
    setImportList(e.target.files[0]);
    // TODO: Implement logic for MAL, Kenmei, AniList, Kitsu, and other sites
  };

  const handleEmailNotificationsToggle = () => {
    setEmailNotifications(!emailNotifications);
  };

  const handlePushNotificationsToggle = () => {
    setPushNotifications(!pushNotifications);
  };

  const handleDeleteAccount = () => {
    if (window.confirm("Are you sure you want to delete your account? This action cannot be undone.")) {
      deleteUserAccount();
    }
  };

  const handleLanguageChange = (e) => {
    setLanguage(e.target.value);
  };

  if (!isLoggedIn) {
    return <div>Please log in to view your profile</div>;
  }

  return (
    <div className={`user-profile ${lightMode ? 'light' : 'dark'}`}>
      <div className="profile-info">
        <img src={profileData.profilePicture} alt="Profile" className="profile-picture" />
        <h2>{profileData.name}</h2>
        <p>{profileData.email}</p>
        <button onClick={() => setEditingProfile(true)}>Edit Profile</button>
        <button onClick={() => setChangingPassword(true)}>Change Password</button>
        <label className="mode-switch">
          <span>Dark Mode</span>
          <input type="checkbox" checked={lightMode} onChange={() => setLightMode(!lightMode)} />
          <span className="slider"></span>
        </label>
        <label className="notifications-toggle">
          <span>Email Notifications</span>
          <input type="checkbox" checked={emailNotifications} onChange={handleEmailNotificationsToggle} />
          <span className="slider"></span>
        </label>
        <label className="notifications-toggle">
          <span>Push Notifications</span>
          <input type="checkbox" checked={pushNotifications} onChange={handlePushNotificationsToggle} />
          <span className="slider"></span>
        </label>
        <label className="import-list">
          Import list from:
          <input type="file" accept=".csv, .xlsx" onChange={handleImportList} />
        </label>
        <label className="language-select">
          <span>Language:</span>
          <select value={language} onChange={handleLanguageChange}>
            <option value="en">English</option>
            <option value="es">Spanish</option>
            <option value="fr">French</option>
            <option value="de">German</option>
            <option value="zh">Chinese</option>
          </select>
        </label>
        <button className="delete-account" onClick={handleDeleteAccount}>Delete Account</button>
      </div>

      {editingProfile && (
        <form className="edit-profile-form" onSubmit={handleProfileSubmit}>
          <label>
            Name:
            <input type="text" name="name" value={profileData.name} onChange={handleProfileChange} />
          </label>
          <label>
            Email:
            <input type="email" name="email" value={profileData.email} onChange={handleProfileChange} />
          </label>
          <label>
            Profile Picture URL:
            <input type="text" name="profilePicture" value={profileData.profilePicture} onChange={handleProfileChange} />
          </label>
          <button type="submit">Save</button>
          <button type="button" onClick={() => setEditingProfile(false)}>Cancel</button>
        </form>
      )}

      {changingPassword && (
        <form className="change-password-form" onSubmit={handlePasswordSubmit}>
          <label>
            Current Password:
            <input type="password" name="currentPassword" value={passwordData.currentPassword} onChange={handlePasswordChange} />
          </label>
          <label>
            New Password:
            <input type="password" name="newPassword" value={passwordData.newPassword} onChange={handlePasswordChange} />
          </label>
          <label>
            Confirm New Password:
            <input type="password" name="confirmPassword" value={passwordData.confirmPassword} onChange={handlePasswordChange} />
          </label>
          <button type="submit">Change Password</button>
          <button type="button" onClick={() => setChangingPassword(false)}>Cancel</button>
        </form>
      )}
    </div>
  );
};

export default UserProfile;