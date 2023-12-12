import React, { useState, useEffect } from 'react';
import axios from 'axios';
import { useAuth } from './AuthContext';
import './AddBookToTracker.scss';

const AddBookToTracker = ({ onBookAdded, onClose, givenBookTitle }) => {
    const [bookTitle, setBookTitle] = useState('');
    const [readingStatus, setReadingStatus] = useState('');
    const [userTags, setUserTags] = useState('');
    const [latestReadChapter, setLatestReadChapter] = useState('');
    const { user } = useAuth();

    // Only update bookTitle when givenBookTitle changes
    useEffect(() => {
        if (givenBookTitle) {
            setBookTitle(givenBookTitle);
        }
    }, [givenBookTitle]);

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
                await axios.put(`http://127.0.0.1:8000/centralized_API_backend/api/profiles/update_reading_list/`, {
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
                        : <input 
                            className='formInput'
                            type="text" 
                            value={bookTitle} 
                            onChange={(e) => setBookTitle(e.target.value)} 
                            placeholder="Book Title" 
                          />
                    }
                    <select
                        className='formInput'
                        value={readingStatus}
                        onChange={(e) => setReadingStatus(e.target.value)}
                    >
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
            </div>
        </div>
    );
};

export default AddBookToTracker;
