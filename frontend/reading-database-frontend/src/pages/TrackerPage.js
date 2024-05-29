import React, { useState, useEffect } from 'react';
import TrackerTable from '../components/TrackerTable';
import { useAuth } from '../components/AuthContext';
import './TrackerPage.scss';

const TrackerPage = () => {
  const [trackingList, setTrackingList] = useState([]);
  const [titleQuery, setTitleQuery] = useState('');                     // Solo Leveling, Absolute _, etc.
  const [sourceQuery, setSourceQuery] = useState('');                   // AsuraScans, LightNovelPub, etc.
  const [typeQuery, setTypeQuery] = useState('');                       // Manhwa, Manhua, Light Novel, etc.
  const [readingStatusQuery, setReadingStatusQuery] = useState('');     // Reading, Dropped, Completed, etc.
  const [userTagQuery, setUserTagQuery] = useState('');

  const [bookSource, setBookSource] = useState([]);
  const [bookType, setBookType] = useState([]);
  const [readingStatus, setReadingStatus] = useState([]);
  const [userTags, setUserTags] = useState([]);

  const { user } = useAuth();

  const filteredBooks = trackingList && trackingList.filter(book =>
    book.title?.toLowerCase().includes(titleQuery.toLowerCase()) 
    && book.novel_source?.toLowerCase().includes(sourceQuery.toLowerCase()) 
    && book.novel_type?.toLowerCase().includes(typeQuery.toLowerCase()) 
    && book.reading_status?.toLowerCase().includes(readingStatusQuery.toLowerCase()) 
    && book.user_tag?.toLowerCase().includes(userTagQuery.toLowerCase()) 
  );

  const extractUniqueAttributes = (trackingList, attribute) => {
    const allAttributes = trackingList.flatMap(book => book[attribute] || []);
    return [...new Set(allAttributes)];
  };

  const fetchTrackingList = async () => {
    if (user) {
      try {
        const encodedEmail = encodeURIComponent(user.username);
        const response = await fetch(`/centralized_API_backend/api/profiles/${encodedEmail}/tracking_list`);
        if (!response.ok) {
          throw new Error(`HTTP error! status: ${response.status}`);
        }
        const data = await response.json();
        // console.log(data.reading_list);
        setTrackingList(data.reading_list);
        // const readingList = JSON.parse(data.reading_list);
        // setTrackingList(readingList);
        setBookSource(extractUniqueAttributes(data.reading_list, 'novel_source'));
        setBookType(extractUniqueAttributes(data.reading_list, 'novel_type'));
        setUserTags(extractUniqueAttributes(data.reading_list, 'user_tag'));
        setReadingStatus(extractUniqueAttributes(data.reading_list, 'reading_status'));
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
      {user && user.profileName
        ? <h1>{user.profileName}'s Tracking List</h1>
        : <h1>User's Tracking List</h1>
      }
      <input
        type="text"
        placeholder="Search books by title"
        value={titleQuery}
        onChange={(e) => setTitleQuery(e.target.value)}
      />
      <select
        value={sourceQuery}
        onChange={(e) => setSourceQuery(e.target.value)}
      >
        <option value="">All Book Sources</option>
        {bookSource.map((source, index) => (
          <option key={index} value={source}>{source}</option>
        ))}
      </select>
      <select
        value={typeQuery}
        onChange={(e) => setTypeQuery(e.target.value)}
      >
        <option value="">All Book Types</option>
        {bookType.map((type, index) => (
          <option key={index} value={type}>{type}</option>
        ))}
      </select>
      <select
        value={readingStatusQuery}
        onChange={(e) => setReadingStatusQuery(e.target.value)}
      >
        <option value="">All Reading Status</option>
        {readingStatus.map((status, index) => (
          <option key={index} value={status}>{status}</option>
        ))}
      </select>
      <select
        value={userTagQuery}
        onChange={(e) => setUserTagQuery(e.target.value)}
      >
        <option value="">All User Tags</option>
        {userTags.map((tag, index) => (
          <option key={index} value={tag}>{tag}</option>
        ))}
      </select>
      <TrackerTable books={filteredBooks} fetchTrackingList={fetchTrackingList} onBookEdited={handleBookChanged} />
    </div>
  );
};

export default TrackerPage;
