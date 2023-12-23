import React, { useState, useEffect } from 'react';
import axios from 'axios';
import './FindBookForTracker.scss';

const FindBookForTracker = ({ onBookSelect, onClose }) => {
    const [bookTitle, setBookTitle] = useState('');
    const [searchResults, setSearchResults] = useState([]);
    const [loading, setLoading] = useState(false);
    const [error, setError] = useState('');

    const API_ENDPOINT = 'http://127.0.0.1:8000';

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
            // TODO: Ideally this should not be "manga" but all the novels (from AsuraScans and LightNovelPub)
            const mangaResponse = await axios.get(`${API_ENDPOINT}/centralized_API_backend/api/all-novels/search`, {
                params: { title: title }
            });
            // const lightNovelResponse = await axios.get(`${API_ENDPOINT}/centralized_API_backend/api/lightnovel/search`, {
            //     params: { title: title }
            // });

            // TODO: Could handle this differently (maybe most popular books?)
            // setSearchResults(response.data.slice(0, 5));
            setSearchResults(mangaResponse.data);
            // setSearchResults(...lightNovelResponse.data);
            // if (mangaResponse.data.length === 0 && lightNovelResponse.data.length === 0) {
            if (mangaResponse.data.length === 0) {
                    setError('No results found');
            }
        } catch (error) {
            setError('Failed to fetch results');
        } finally {
            setLoading(false);
        }
    };

    const handleSelectBook = (selectedBook) => {
        setBookTitle(selectedBook.title);
        setSearchResults([]);
        onBookSelect(selectedBook);
    };

    return (
        <div className="modalBackdrop">
            <div className="modalContent">
                <button className='closeButton' onClick={onClose}>X</button>
                <div>
                    <input 
                        className='formInput'
                        type="text" 
                        value={bookTitle} 
                        onChange={(e) => { setBookTitle(e.target.value) }} 
                        autoComplete="off"
                        placeholder="Book Title" 
                    />
                    <div className="searchResults">
                        {loading && <div>Loading...</div>}
                        {error && <div>{error}</div>}
                        {!loading && searchResults.map((book) => (
                            <div key={book.id} className="searchResultItem" onClick={() => handleSelectBook(book)}>
                                <img src={book.image_url} alt={book.title} />
                                <div className="book-details">
                                <div className="book-title">{book.title}</div>
                                <div className="book-chapters">
                                    {book.novel_source !== "Light Novel Pub" && "Chapter"} {book.newest_chapter}
                                </div>
                                <div className="book-chapters">Source: {book.novel_source}</div>
                                <div className="book-genres">
                                    {book.genres.map((genre, index) => (
                                    <span key={index} className="genre">{genre}</span>
                                    ))}
                                </div>
                                </div>
                            </div>
                        ))}
                    </div>
                </div>
            </div>
        </div>
    );
};

export default FindBookForTracker;
