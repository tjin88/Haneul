import React, { useState } from 'react';
import axios from 'axios';
import { useAuth } from './AuthContext';

const AddBookToTracker = ({ onBookAdded }) => {
    const [bookTitle, setBookTitle] = useState('');
    const [readingStatus, setReadingStatus] = useState('');
    const [userTags, setUserTags] = useState('');
    const [latestReadChapter, setLatestReadChapter] = useState('');
    const { user } = useAuth();

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
                
                // Update the tracking list in parent component
                onBookAdded();
    
                // Reset the input fields
                setBookTitle('');
                setReadingStatus('');
                setUserTags('');
                setLatestReadChapter('');
            } catch (error) {
                console.error('Error adding book to tracker:', error);
            }
        } else {
            console.error('User not authenticated');
        }
    };
    

    return (
        <form onSubmit={handleSubmit}>
            <input 
                type="text" 
                value={bookTitle} 
                onChange={(e) => setBookTitle(e.target.value)} 
                placeholder="Book Title" 
            />
            <input 
                type="text" 
                value={readingStatus} 
                onChange={(e) => setReadingStatus(e.target.value)} 
                placeholder="Reading Status" 
            />
            <input 
                type="text" 
                value={userTags} 
                onChange={(e) => setUserTags(e.target.value)} 
                placeholder="User Tags" 
            />
            <input 
                type="text" 
                value={latestReadChapter} 
                onChange={(e) => setLatestReadChapter(e.target.value)} 
                placeholder="Latest Read Chapter" 
            />
            <button type="submit">Add Book</button>
        </form>
    );
};

export default AddBookToTracker;
