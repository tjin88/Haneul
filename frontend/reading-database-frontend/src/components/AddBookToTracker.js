import React, { useState, useEffect } from 'react';
import axios from 'axios';
import { useAuth } from './AuthContext';
import './AddBookToTracker.scss';

const AddBookToTracker = ({ onBookAdded, onClose, sendBack, givenBook }) => {
    const [bookTitle, setBookTitle] = useState('');
    const [readingStatus, setReadingStatus] = useState('');
    const [userTags, setUserTags] = useState('');
    const [latestReadChapter, setLatestReadChapter] = useState('');
    const { user } = useAuth();

    const API_ENDPOINT = 'http://127.0.0.1:8000';

    const chaptersArray = givenBook ? Object.keys(givenBook.chapters) : [];

    // Only used when book title is given (direct from book page)
    useEffect(() => {
        if (givenBook) {
            setBookTitle(givenBook.title);
        }
    }, [givenBook]);

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
                    chapter_link: givenBook.chapters[latestReadChapter],
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
                <button className='backButton' onClick={sendBack}>BACK</button>
                <button className='closeButton' onClick={onClose}>X</button>
                <form onSubmit={handleSubmit}>
                    {givenBook 
                        ? <div className="searchResultItem">
                            <img src={givenBook.image_url} alt={givenBook.title} />
                            <div className="book-details">
                            <div className="book-title">{givenBook.title}</div>
                            <div className="book-chapters">{givenBook.newest_chapter} chapters</div>
                            <div className="book-genres">
                                {givenBook.genres.map((genre, index) => (
                                <span key={index} className="genre">{genre}</span>
                                ))}
                            </div>
                            </div>
                        </div>
                        : <p className='givenBookTitle'>ERROR: Please refresh the page and try again</p>
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
                    <select
                        className='formInput'
                        value={latestReadChapter}
                        onChange={(e) => setLatestReadChapter(e.target.value)}
                    >   
                        <option value="" disabled>Latest Read Chapter</option>
                        {chaptersArray.map((chapter, index) => (
                            <option key={index} value={chapter}>Chapter {chapter}</option>
                        ))}
                    </select>
                    <button className="formButton" type="submit">Add Book</button>
                </form>
            </div>
        </div>
    );
};

export default AddBookToTracker;
