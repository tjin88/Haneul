import React, { useState, useEffect } from 'react';
import TrackerTable from '../components/TrackerTable';
import { useAuth } from '../components/AuthContext';
import './TrackerPage.scss';

const TrackerPage = () => {
  const [trackingList, setTrackingList] = useState([]);
  const { user } = useAuth();

  const API_ENDPOINT = 'http://127.0.0.1:8000';

  const fetchTrackingList = async () => {
    if (user) {
      try {
        const encodedEmail = encodeURIComponent(user.username);
        const response = await fetch(`${API_ENDPOINT}/centralized_API_backend/api/profiles/${encodedEmail}/tracking_list`);
        if (!response.ok) {
          throw new Error(`HTTP error! status: ${response.status}`);
        }
        const data = await response.json();
        setTrackingList(data.reading_list);
      } catch (error) {
        console.error('Error fetching tracking list:', error);
      }
    }
  };

  useEffect(() => {
    fetchTrackingList();
  }, [user]);

  const handleBookChanged = () => {
    fetchTrackingList(); 
  };

  return (
    <div className='trackerPage'>
      {/* <h1>{user.profileName}'s Tracking List</h1> */}
      {user && user.profileName 
        ? <h1>{user.profileName}'s Tracking List</h1>
        : <h1>User's Tracking List</h1>
      }
      <TrackerTable books={trackingList} fetchTrackingList={fetchTrackingList} onBookEdited={handleBookChanged} />
    </div>
  );
};

export default TrackerPage;
