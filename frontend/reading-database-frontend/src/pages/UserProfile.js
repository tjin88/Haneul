import React, { useState, useEffect } from 'react';
import { useAuth } from '../components/AuthContext';
import ManColour from '../assets/ManColour.png';
import './UserProfile.scss';

const UserProfile = ({ lightMode, setLightMode }) => {
  const { isLoggedIn, user, updateUserProfile, changeUserPassword, deleteUserAccount } = useAuth();
  const [editingProfile, setEditingProfile] = useState(false);
  const [changingPassword, setChangingPassword] = useState(false);

  const [profileData, setProfileData] = useState({
    name: '',
    email: '',
    profileImage: '',
    emailNotifications: false,
    pushNotifications: false,
    language: 'en',
  });

  const [passwordData, setPasswordData] = useState({
    currentPassword: '',
    newPassword: '',
    confirmPassword: ''
  });

  // const [importList, setImportList] = useState(null);
  const [profileImageFile, setProfileImageFile] = useState(null);

  useEffect(() => {
    if (user) {
      setProfileData({
        name: user.profileName,
        email: user.username,
        profileImage: user.profileImage,
        emailNotifications: user.emailNotifications,
      });
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
    const formData = new FormData();
    formData.append('name', profileData.name);
    formData.append('email', profileData.email);
    formData.append('emailNotifications', profileData.emailNotifications);
    if (profileImageFile) {
      formData.append('profileImage', profileImageFile);
    }

    updateUserProfile(formData);
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

  const handleDeleteAccount = () => {
    if (window.confirm("Are you sure you want to delete your account? This action cannot be undone.")) {
      deleteUserAccount();
    }
  };

  // const handleImportList = (e) => {
  //   setImportList(e.target.files[0]);
  //   // TODO: Implement logic for MAL, Kenmei, AniList, Kitsu, and other sites
  // };

  const handleEmailNotificationsToggle = () => {
    setProfileData(prevState => ({
      ...prevState,
      emailNotifications: !prevState.emailNotifications
    }));
  };

  const handleDarkModeToggle = () => {
    setLightMode(!lightMode);
  };

  const handleProfileImageChange = (e) => {
    setProfileImageFile(e.target.files[0]);
    const reader = new FileReader();
    reader.onload = () => {
      setProfileData(prevState => ({
        ...prevState,
        profileImage: reader.result
      }));
    };
    reader.readAsDataURL(e.target.files[0]);
  };

  if (!isLoggedIn) {
    return <div>Please log in to view your profile</div>;
  }

  return (
    <div className={`user-profile ${lightMode ? 'light' : 'dark'}`}>
      <nav className="profile-nav">
        <ul>
          <li><button onClick={() => setEditingProfile(!editingProfile)}>Edit Profile</button></li>
          <li><button onClick={() => setChangingPassword(!changingPassword)}>Change Password</button></li>
          <li><button onClick={handleDeleteAccount} className="delete-account">Delete Account</button></li>
        </ul>
      </nav>
      <div className="profile-content">
        <div className="profile-left">
          <img src={profileData.profileImage || ManColour} alt="Profile" className="profile-picture" />
          <h2>{profileData.name}</h2>
          <p>{profileData.email}</p>
        </div>
        <div className="profile-right">
          <label className="mode-switch">
            <span>Dark Mode</span>
            <input type="checkbox" checked={lightMode} onChange={handleDarkModeToggle} />
            <span className="slider"></span>
          </label>
          <label className="notifications-toggle">
            <span>Email Notifications</span>
            <input type="checkbox" checked={profileData.emailNotifications} onChange={handleEmailNotificationsToggle} />
            <span className="slider"></span>
          </label>
          {/* <label className="import-list">
            Import list from:
            <input type="file" accept=".csv, .xlsx, .json" onChange={handleImportList} />
          </label> */}
        </div>
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
            Profile Picture:
            <input type="file" name="profileImage" accept="image/*" onChange={handleProfileImageChange} />
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