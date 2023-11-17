import React, { useState } from 'react';
import './Browse.scss';

const Browse = ({ books, lightMode }) => {
  const [searchTerm, setSearchTerm] = useState('');
  const [sortType, setSortType] = useState('default');
  const [genreFilter, setGenreFilter] = useState('');

  const handleSearchChange = (e) => {
    setSearchTerm(e.target.value);
  };

  const handleGenreChange = (e) => {
    setGenreFilter(e.target.value);
  };

  // Filter books based on search term, type, and genre
  let filteredBooks = books.filter(book =>
    book.title.toLowerCase().includes(searchTerm.toLowerCase()) &&
    (genreFilter ? book.genres.includes(genreFilter) : true)
  );

  // If a specific manga_type is selected, filter the books to only that type
  if (['manga', 'manhua', 'manhwa'].includes(sortType)) {
    filteredBooks = filteredBooks.filter(book => book.manga_type === sortType.charAt(0).toUpperCase() + sortType.slice(1));
  }

  // Sort filteredBooks based on the selected sortType
  filteredBooks = filteredBooks.sort((a, b) => {
    switch (sortType) {
      case 'rating':
        return parseFloat(b.rating) - parseFloat(a.rating);
      case 'newest':
        return new Date(b.posted_on) - new Date(a.posted_on);
      case 'updated':
        return new Date(b.updated_on) - new Date(a.updated_on);
      case 'followers':
        return parseInt(b.followers.split(' ')[2].replace(/,/g, '')) - parseInt(a.followers.split(' ')[2].replace(/,/g, ''));
      case 'chapters':
        return Object.keys(b.chapters).length - Object.keys(a.chapters).length;
      default:
        return 0;
    }
  });

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
        {filteredBooks.map((book, index) => (
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
