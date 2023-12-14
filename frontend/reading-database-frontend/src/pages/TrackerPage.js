import React, { useState, useEffect } from 'react';
import axios from 'axios';
import TrackerTable from '../components/TrackerTable';
import { useAuth } from '../components/AuthContext';
import FindBookForTracker from '../components/FindBookForTracker';
import AddBookToTracker from '../components/AddBookToTracker';
import './TrackerPage.scss';

const TrackerPage = () => {
  const [trackingList, setTrackingList] = useState([]);
  const [showModal, setShowModal] = useState(false);
  const [selectedBook, setSelectedBook] = useState(null);
  const { user } = useAuth();

  const API_ENDPOINT = 'http://127.0.0.1:8000';

  const fetchTrackingList = async () => {
    if (user) {
      try {
          const encodedEmail = encodeURIComponent(user.username);
          const response = await axios.get(`${API_ENDPOINT}/centralized_API_backend/api/profiles/${encodedEmail}/tracking_list`);
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

  const handleCloseModal = () => {
    setSelectedBook(null);
    setShowModal(false);
  };

  const handleBookSelect = (book) => {
    setSelectedBook(book);
  };

  const handleSendBack = () => {
    setSelectedBook(null);
  };

  return (
    <div className='trackerPage'>
      <h1>My Tracking List</h1>
        <button className='addButton' onClick={() => setShowModal(true)}>Add Book</button>
        {showModal && !selectedBook && <FindBookForTracker onBookSelect={handleBookSelect} onClose={handleCloseModal} />}
        {showModal && selectedBook && 
          <AddBookToTracker
            onBookAdded={handleBookAdded}
            onClose={handleCloseModal}
            sendBack={handleSendBack}
            givenBook={selectedBook}
          />
        }
        <TrackerTable books={trackingList} />
    </div>
  );
};

export default TrackerPage;
