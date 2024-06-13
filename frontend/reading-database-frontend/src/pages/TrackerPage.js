import React, { useState, useEffect } from 'react';
import TrackerTable from '../components/TrackerTable';
import Select from 'react-select';
import makeAnimated from 'react-select/animated';
import { useAuth } from '../components/AuthContext';
// import { useCsrf } from '../components/CsrfContext';
import './TrackerPage.scss';

const TrackerPage = () => {
  const [trackingList, setTrackingList] = useState([]);
  const [titleQuery, setTitleQuery] = useState('');
  const [sourceQuery, setSourceQuery] = useState([]);
  const [typeQuery, setTypeQuery] = useState([]);
  const [readingStatusQuery, setReadingStatusQuery] = useState([]);
  const [userTagQuery, setUserTagQuery] = useState([]);

  const [bookSource, setBookSource] = useState([]);
  const [bookType, setBookType] = useState([]);
  const [readingStatus, setReadingStatus] = useState([]);
  const [userTags, setUserTags] = useState([]);

  // const { csrfToken, getCsrfToken } = useCsrf();
  const { user } = useAuth();
  const animatedComponents = makeAnimated();

  const filteredBooks = trackingList && trackingList.filter(book =>
    book.title?.toLowerCase().includes(titleQuery.toLowerCase()) &&
    (sourceQuery.length === 0 || sourceQuery.some(source => book.novel_source?.toLowerCase() === source.value.toLowerCase())) &&
    (typeQuery.length === 0 || typeQuery.some(type => book.novel_type?.toLowerCase() === type.value.toLowerCase())) &&
    (readingStatusQuery.length === 0 || readingStatusQuery.some(status => book.reading_status?.toLowerCase() === status.value.toLowerCase())) &&
    (userTagQuery.length === 0 || userTagQuery.some(tag => book.user_tag?.toLowerCase() === tag.value.toLowerCase()))
  );

  const extractUniqueAttributes = (trackingList, attribute) => {
    const allAttributes = trackingList.flatMap(book => book[attribute] || []);
    return [...new Set(allAttributes)];
  };

  const fetchTrackingList = async () => {
    if (user) {
      try {
        // await getCsrfToken();
        const encodedEmail = encodeURIComponent(user.username);
        const token = localStorage.getItem('token');
        const response = await fetch(`${process.env.REACT_APP_API_URL}/centralized_API_backend/api/profiles/${encodedEmail}/tracking_list/`, {
          method: 'GET',
          headers: {
              'Authorization': `Bearer ${token}`,
              'Content-Type': 'application/json'
          },
          credentials: 'include'
        });
        if (!response.ok) {
          throw new Error(`HTTP error! status: ${response.status}`);
        }
        const data = await response.json();
        setTrackingList(data.reading_list);
        setBookSource(extractUniqueAttributes(data.reading_list, 'novel_source').map(source => ({ value: source, label: source })));
        setBookType(extractUniqueAttributes(data.reading_list, 'novel_type').map(type => ({ value: type, label: type })));
        setUserTags(extractUniqueAttributes(data.reading_list, 'user_tag').map(tag => ({ value: tag, label: tag })));
        setReadingStatus(extractUniqueAttributes(data.reading_list, 'reading_status').map(status => ({ value: status, label: status })));
      } catch (error) {
        console.error('Error fetching tracking list:', error);
      }
    }
  };

  useEffect(() => {
    fetchTrackingList();
  // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [user]);

  const handleBookChanged = () => {
    fetchTrackingList();
  };

  const handleSourceChange = (selectedOptions) => {
    setSourceQuery(selectedOptions || []);
  };

  const handleTypeChange = (selectedOptions) => {
    setTypeQuery(selectedOptions || []);
  };

  const handleStatusChange = (selectedOptions) => {
    setReadingStatusQuery(selectedOptions || []);
  };

  const handleTagChange = (selectedOptions) => {
    setUserTagQuery(selectedOptions || []);
  };

  return (
    <div className='trackerPage'>
      {user && user.profileName
        ? <h1>{user.profileName}'s Tracking List</h1>
        : <h1>User's Tracking List</h1>
      }
      <div className='filters'>
        <input
          className='title_filter'
          type="text"
          placeholder="Search books by title"
          value={titleQuery}
          onChange={(e) => setTitleQuery(e.target.value)}
        />
        <Select
          isMulti
          components={animatedComponents}
          value={sourceQuery}
          onChange={handleSourceChange}
          options={bookSource}
          className="select"
          placeholder="Select sources..."
        />
        <Select
          isMulti
          components={animatedComponents}
          value={typeQuery}
          onChange={handleTypeChange}
          options={bookType}
          className="select"
          placeholder="Select types..."
        />
        <Select
          isMulti
          components={animatedComponents}
          value={readingStatusQuery}
          onChange={handleStatusChange}
          options={readingStatus}
          className="select"
          placeholder="Select reading statuses..."
        />
        <Select
          isMulti
          components={animatedComponents}
          value={userTagQuery}
          onChange={handleTagChange}
          options={userTags}
          className="select"
          placeholder="Select user tags..."
        />
      </div>
      <TrackerTable books={filteredBooks} fetchTrackingList={fetchTrackingList} onBookEdited={handleBookChanged} />
    </div>
  );
};

export default TrackerPage;
