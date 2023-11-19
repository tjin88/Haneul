import React, { useState, useEffect } from 'react';
import axios from 'axios';
import TrackerTable from '../components/TrackerTable';
import { useAuth } from '../components/AuthContext';
import AddBookToTracker from '../components/AddBookToTracker';

const TrackerPage = () => {
  const [trackingList, setTrackingList] = useState([]);
  const { user } = useAuth();

  const fetchTrackingList = async () => {
    if (user) {
      try {
          const encodedEmail = encodeURIComponent(user.username);
          const response = await axios.get(`http://127.0.0.1:8000/centralized_API_backend/api/profiles/${encodedEmail}/tracking_list`);
          setTrackingList(response.data.reading_list);
      } catch (error) {
        console.error('Error fetching tracking list:', error);
      }
    }
  };

  useEffect(() => {
    fetchTrackingList();
  }, [user]);

  // Refetch the tracking list
  const handleBookAdded = () => {
    fetchTrackingList(); 
  };

  return (
    <div>
      <h1>My Tracking List</h1>
      <AddBookToTracker onBookAdded={handleBookAdded} />
      <TrackerTable books={trackingList} />
    </div>
  );
};

export default TrackerPage;
