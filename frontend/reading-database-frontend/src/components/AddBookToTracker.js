import React, { useState, useEffect } from 'react';
import { useAuth } from './AuthContext';
// import { useCsrf } from './CsrfContext';
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
    // const { csrfToken, getCsrfToken } = useCsrf();
    const [bookChapters, setBookChapters] = useState({});
    const img_placeholder = "https://via.placeholder.com/400x600/CCCCCC/FFFFFF?text=No+Image";
    const [imageUrl, setImageUrl] = useState(img_placeholder);

    const fetchBookDetails = async (title, source) => {
        try {
            const response = await fetch(`${process.env.REACT_APP_API_URL}/centralized_API_backend/api/all-novels/search?title=${encodeURIComponent(title)}&novel_source=${encodeURIComponent(source)}`);
            if (!response.ok) {
                throw new Error(`HTTP error! status: ${response.status}`);
            }
            return await response.json();
        } catch (error) {
            console.error('Error fetching book details:', error);
            return null;
        }
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
                        // 'X-CSRFToken': csrfToken,
                        'Content-Type': 'application/json'
                    },
                    credentials: 'include'
                });
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

    const handleImageError = () => {
        setImageUrl(img_placeholder);
    };

    useEffect(() => {
        fetchTrackingList();
    }, [user]);

    useEffect(() => {
        if (givenBook) {
            setBookTitle(givenBook.title);

            const loadBookDetails = async () => {
                if (givenBook && (!givenBook.chapters || !givenBook.genres)) {
                    const book = await fetchBookDetails(givenBook.title, givenBook.novel_source);
                    if (book && book[0]) {
                        setBookDetails(book[0]);
                        setImageUrl(book[0].image_url || img_placeholder);
                    } else {
                        console.error("Error setting book!");
                    }
                } else {
                    setBookDetails(givenBook);
                    setImageUrl(givenBook.image_url || img_placeholder);
                }
            };
            loadBookDetails();
        }
    }, [givenBook]);

    useEffect(() => {
        if (bookDetails) {
            try {
                if (typeof bookDetails.chapters === 'string') {
                    setBookChapters(JSON.parse(bookDetails.chapters));
                } else { 
                    setBookChapters(bookDetails.chapters); 
                }
            } catch (error) {
                console.error('Error parsing chapters:', error);
            }

            const bookInList = trackingList.find(book => book.title === givenBook.title && book.novel_source === givenBook.novel_source);
            if (bookInList) {
                setReadingStatus(bookInList.reading_status);
                setUserTags(bookInList.user_tag);
                setLatestReadChapter(bookInList.latest_read_chapter);
                setIsEditting(true);
            }
        }
    }, [bookDetails, givenBook, trackingList]);

    const handleSubmit = async (e) => {
        e.preventDefault();

        if (!bookTitle || !readingStatus || !latestReadChapter) {
            alert('Please fill in all fields');
            return;
        }

        if (user) {
            try {
                // await getCsrfToken();
                const token = localStorage.getItem('token');
                const response = await fetch(`${process.env.REACT_APP_API_URL}/centralized_API_backend/api/profiles/update_reading_list/`, {
                    method: 'PUT',
                    headers: {
                        'Authorization': `Bearer ${token}`,
                        // 'X-CSRFToken': csrfToken,
                        'Content-Type': 'application/json'
                    },
                    credentials: 'include',
                    body: JSON.stringify({
                        username: user.username,
                        title: bookTitle,
                        reading_status: readingStatus,
                        user_tag: userTags,
                        latest_read_chapter: latestReadChapter,
                        novel_source: givenBook.novel_source,
                    }),
                });

                if (!response.ok) {
                    throw new Error(`HTTP error! status: ${response.status}`);
                }

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
                            <img src={imageUrl} alt={bookDetails.title} onError={handleImageError} />
                            <div className="book-details">
                            <div className="book-title">{bookDetails.title}</div>
                            <div className="book-chapters">
                                {bookDetails.novel_source !== "Light Novel Pub" && "Chapter"} {bookDetails.newest_chapter}
                            </div>
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
                    {bookChapters && <select
                        className='formInput'
                        value={latestReadChapter}
                        onChange={(e) => setLatestReadChapter(e.target.value)}
                    >   
                        <option value="" disabled>Latest Read Chapter</option>
                        {Object.keys(bookChapters).map((chapter, index) => (
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