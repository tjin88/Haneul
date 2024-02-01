import React, { useState, useEffect } from 'react';
import './Browse.scss';

const Browse = ({ lightMode }) => {
  const [searchTerm, setSearchTerm] = useState('');
  const [sortType, setSortType] = useState('default');
  const [genreFilter, setGenreFilter] = useState('');
  const [books, setBooks] = useState([]);


  useEffect(() => {
    const fetchData = async () => {
      const title = encodeURIComponent(searchTerm);
      const genre = encodeURIComponent(genreFilter);
      const response = await fetch(`/centralized_API_backend/api/all-novels/search?title=${title}&genre=${genre}`);
      const data = await response.json();
      setBooks(data);
    };

    if (searchTerm || genreFilter || sortType !== 'default') {
      fetchData();
    }
  }, [searchTerm, genreFilter, sortType]);

  const handleSearchChange = (e) => {
    setSearchTerm(e.target.value);
  };

  const handleGenreChange = (e) => {
    setGenreFilter(e.target.value);
  };

  return (
    <div className="browse">
      <input
        type="text"
        placeholder="Search by title..."
        value={searchTerm}
        onChange={handleSearchChange}
        className="search-input"
      />
      <input
        type="text"
        placeholder="Search by genre..."
        value={genreFilter}
        onChange={handleGenreChange}
        className="search-input"
      />
      <select onChange={(e) => setSortType(e.target.value)} className="sort-select">
        <option value="default">Sort by...</option>
        <option value="manga">Manga</option>
        <option value="manhua">Manhua</option>
        <option value="manhwa">Manhwa</option>
        <option value="rating">Rating</option>
        <option value="newest">Newest Added</option>
        <option value="updated">Recently Updated</option>
        <option value="followers">Most Followers</option>
        <option value="chapters">Total Chapters</option>
      </select>
      <div className="books-grid">
        {books.map((book, index) => (
          <div key={index} className="book-item">
            <img src={book.image_url} alt={book.title} />
            <div className="book-info">
              <h3>{book.title}</h3>
              <p>Chapter: {book.newest_chapter}</p>
              <p>{book.followers}</p>
              <p>{book.genres.join(', ')}</p>
              <p>Rating: {book.rating}</p>
            </div>
          </div>
        ))}
      </div>
    </div>
  );
};

export default Browse;
