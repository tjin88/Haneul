import React, { useState, useEffect } from 'react';
import axios from 'axios';
import { useAuth } from './AuthContext';
import './AddBookToTracker.scss';

const AddBookToTracker = ({ onBookAdded, onClose, givenBookTitle }) => {
    const [bookTitle, setBookTitle] = useState('');
    const [searchResults, setSearchResults] = useState([]);
    // const [isDropdownVisible, setIsDropdownVisible] = useState(false);
    const [readingStatus, setReadingStatus] = useState('');
    const [userTags, setUserTags] = useState('');
    const [latestReadChapter, setLatestReadChapter] = useState('');
    const [loading, setLoading] = useState(false);
    const [error, setError] = useState('');
    const { user } = useAuth();

    const API_ENDPOINT = 'http://127.0.0.1:8000';

    // Only used when book title is given (direct from book page)
    useEffect(() => {
        if (givenBookTitle) {
            setBookTitle(givenBookTitle);
        }
    }, [givenBookTitle]);

    useEffect(() => {
        // Implementing a debounce function to reduce # of API calls
        const delayDebounceFn = setTimeout(() => {
            if (bookTitle) {
                searchBooks(bookTitle);
            } else {
                setSearchResults([]);
            }
        }, 300);

        return () => clearTimeout(delayDebounceFn);
    }, [bookTitle]);

    const searchBooks = async (title) => {
        setLoading(true);
        setError('');
        try {
            const response = await axios.get(`${API_ENDPOINT}/centralized_API_backend/api/mangas/search`, {
                params: { title: title }
            });

            // TODO: Could handle this differently (maybe most popular books?)
            setSearchResults(response.data.slice(0, 5));
            if (response.data.length === 0) {
                setError('No results found');
            }
        } catch (error) {
            setError('Failed to fetch results');
        } finally {
            setLoading(false);
        }
    };

    const handleSelectBook = (selectedBook) => {
        setBookTitle(selectedBook);
        setSearchResults([]);
    };

    const handleSubmit = async (e) => {
        e.preventDefault();
    
        if (!bookTitle || !readingStatus || !userTags || !latestReadChapter) {
            alert('Please fill in all fields');
            return;
        }
    
        if (user) {
            try {
                console.log("current user's email:")
                console.log(user.username)
                await axios.put(`${API_ENDPOINT}/centralized_API_backend/api/profiles/update_reading_list/`, {
                    username: user.username,
                    title: bookTitle,
                    reading_status: readingStatus,
                    user_tag: userTags,
                    latest_read_chapter: latestReadChapter,
                });
                
                // Update the tracking list in parent component --> If provided*
                if (onBookAdded) {
                    onBookAdded();
                }
    
                // Reset the input fields
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
                <button className='closeButton' onClick={onClose}>X</button>
                <form onSubmit={handleSubmit}>
                    {givenBookTitle 
                        ? <p className='givenBookTitle'>{givenBookTitle}</p>
                        : 
                        <div>
                            <input 
                                className='formInput'
                                type="text" 
                                value={bookTitle} 
                                onChange={(e) => { setBookTitle(e.target.value) }} 
                                autoComplete="off"
                                placeholder="Book Title" 
                                // onBlur={() => setTimeout(() => setIsDropdownVisible(false), 100)} // Hide dropdown when input is not focused
                            />
                            <div className="searchResults">
                                {loading && <div>Loading...</div>}
                                {error && <div>{error}</div>}
                                {!loading && searchResults.map((book) => (
                                    <div key={book.id} onClick={() => handleSelectBook(book.title)}>
                                        {book.title}
                                    </div>
                                ))}
                            </div>
                        </div>
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
                        placeholder="User Tags" 
                    />
                    <input 
                        className='formInput'
                        type="text" 
                        value={latestReadChapter} 
                        onChange={(e) => setLatestReadChapter(e.target.value)} 
                        placeholder="Latest Read Chapter" 
                    />
                    <button className="formButton" type="submit">Add Book</button>
                </form>
                {/* {isDropdownVisible && (
                    <div className="searchResultsDropdown">
                        {searchResults.map(book => (
                            <div key={book.id} onClick={() => handleSelectBook(book.title)}>
                                {book.title}
                            </div>
                        ))}
                    </div>
                )} */}
            </div>
        </div>
    );
};

export default AddBookToTracker;
