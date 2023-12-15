import React, { useState, useEffect } from 'react';
import axios from 'axios';
import { useAuth } from './AuthContext';
import './AddBookToTracker.scss';

const AddBookToTracker = ({ onBookAdded, onClose, sendBack, givenBook }) => {
    const [bookTitle, setBookTitle] = useState('');
    const [readingStatus, setReadingStatus] = useState('');
    const [userTags, setUserTags] = useState('');
    const [latestReadChapter, setLatestReadChapter] = useState('');
    const [trackingList, setTrackingList] = useState([]);
    const [isEditting, setIsEditting] = useState(false);
    const [bookDetails, setBookDetails] = useState(null);
    const { user } = useAuth();

    const API_ENDPOINT = 'http://127.0.0.1:8000';

    const fetchBookDetails = async (title) => {
        try {
            const response = await axios.get(`${API_ENDPOINT}/centralized_API_backend/api/mangas/search`, {
                params: { title: title }
            });
            return response.data;
        } catch (error) {
            console.error('Error fetching book details:', error);
            return null;
        }
    };

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

    useEffect(() => {
        if (givenBook) {
            setBookTitle(givenBook.title);
            const loadBookDetails = async () => {
                if (givenBook && (!givenBook.chapters || !givenBook.genres)) {
                    const book = await fetchBookDetails(givenBook.title);
                    if (book && book[0]) {
                        setBookDetails(book[0]);
                    } else {
                        console.error("Error setting book!");
                    }
                } else {
                    setBookDetails(givenBook);
                }
            };
            loadBookDetails();

            const bookInList = trackingList.find(book => book.title === givenBook.title);

            if (bookInList) {
                setReadingStatus(bookInList.reading_status);
                setUserTags(bookInList.user_tag);
                setLatestReadChapter(bookInList.latest_read_chapter);
                setIsEditting(true);
            }
        }
    }, [givenBook, trackingList]);

    const handleSubmit = async (e) => {
        e.preventDefault();
    
        if (!bookTitle || !readingStatus || !latestReadChapter) {
            alert('Please fill in all fields');
            return;
        }
    
        if (user) {
            try {
                await axios.put(`${API_ENDPOINT}/centralized_API_backend/api/profiles/update_reading_list/`, {
                    username: user.username,
                    title: bookTitle,
                    reading_status: readingStatus,
                    user_tag: userTags,
                    latest_read_chapter: latestReadChapter,
                    chapter_link: bookDetails.chapters[latestReadChapter],
                    novel_type: givenBook.novel_type,
                });
                
                if (onBookAdded) {
                    onBookAdded();
                }
    
                setBookTitle('');
                setReadingStatus('');
                setUserTags('');
                setLatestReadChapter('');

                onClose();
            } catch (error) {
                console.error('Error adding book to tracker:', error);
            }
        } else {
            console.error('User not authenticated');
        }
    };

    return (
        <div className="modalBackdrop">
            <div className="modalContent">
                <button className='backButton' onClick={sendBack}>BACK</button>
                <button className='closeButton' onClick={onClose}>X</button>
                <form onSubmit={handleSubmit}>
                    {bookDetails
                        ? <div className="searchResultItem">
                            <img src={bookDetails.image_url} alt={bookDetails.title} />
                            <div className="book-details">
                            <div className="book-title">{bookDetails.title}</div>
                            <div className="book-chapters">{bookDetails.newest_chapter} chapters</div>
                            <div className="book-genres">
                                {bookDetails.genres && bookDetails.genres.map((genre, index) => (
                                <span key={index} className="genre">{genre}</span>
                                ))}
                            </div>
                            </div>
                        </div>
                        : <p className='givenBookTitle'>Loading Book Details ...</p>
                    }
                    <select
                        className='formInput'
                        value={readingStatus}
                        onChange={(e) => setReadingStatus(e.target.value)}
                    >   
                        <option value="" disabled>Reading Status</option>
                        <option value="Reading">Reading</option>
                        <option value="Plan-to-Read">Plan-to-Read</option>
                        <option value="On-Hold">On-Hold</option>
                        <option value="Completed">Completed</option>
                        <option value="Dropped">Dropped</option>
                    </select>
                    <input 
                        className='formInput'
                        type="text" 
                        value={userTags} 
                        onChange={(e) => setUserTags(e.target.value)} 
                        placeholder="User Tag (optional)" 
                    />
                    {bookDetails && bookDetails.chapters && <select
                        className='formInput'
                        value={latestReadChapter}
                        onChange={(e) => setLatestReadChapter(e.target.value)}
                    >   
                        <option value="" disabled>Latest Read Chapter</option>
                        {Object.keys(bookDetails.chapters).map((chapter, index) => (
                            <option key={index} value={chapter}>Chapter {chapter}</option>
                        ))}
                    </select>}
                    <button className="formButton" type="submit">{isEditting ? "Edit" : "Add"} Book</button>
                </form>
            </div>
        </div>
    );
};

export default AddBookToTracker;
