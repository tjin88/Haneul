import React, { useState, useEffect } from 'react';
import './Browse.scss';

const Browse = ({ lightMode }) => {
  const [searchTerm, setSearchTerm] = useState('');
  const [sortType, setSortType] = useState('');
  const [genreFilter, setGenreFilter] = useState('');
  const [books, setBooks] = useState([]);
  const [isFetching, setIsFetching] = useState(false);
  const [error, setError] = useState('');

  useEffect(() => {
    const fetchData = async () => {
      setIsFetching(true);
      const title = encodeURIComponent(searchTerm);
      const genre = encodeURIComponent(genreFilter);

      // TODO: Add the sortType to the API call ***
      // const response = await fetch(`/centralized_API_backend/api/all-novels/browse?title=${title}&genre=${genre}&sortType=${sortType}`);
      const response = await fetch(`/centralized_API_backend/api/all-novels/browse?title=${title}&genre=${genre}`);
      const data = await response.json();
      if (data.length === 0) {
        setError('No books matching the search criteria found!');
      } else {
        setError('');
      }
      setBooks(data);
      setIsFetching(false);
    };

    const debounceFetchData = setTimeout(() => {
      if ((searchTerm.length >= 3 || genreFilter)) {
        setError('');
        fetchData();
      } else if (sortType !== '') {
        setBooks([]);
        setError('Please search (with 3 or more characters) or add a genre!');
      } else if (searchTerm.length > 0 && searchTerm.length < 3) {
        setBooks([]);
        setError('Please enter a search with 3 or more characters!');
      } else {
        setError('');
      }
    }, 500); // 500ms delay

    return () => clearTimeout(debounceFetchData); 
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
        placeholder="Search by title (3 characters minimum)"
        value={searchTerm}
        onChange={handleSearchChange}
        className="search-input"
      />
      <input
        type="text"
        placeholder="Search by genre (Full genre name)"
        value={genreFilter}
        onChange={handleGenreChange}
        className="search-input"
      />
      <select onChange={(e) => setSortType(e.target.value)} className="sort-select">
        <option value="">Sort by...</option>
        <option value="manga">Manga</option>
        <option value="manhua">Manhua</option>
        <option value="manhwa">Manhwa</option>
        <option value="rating">Rating</option>
        <option value="newest">Newest Added</option>
        <option value="updated">Recently Updated</option>
        <option value="followers">Most Followers</option>
        <option value="chapters">Total Chapters</option>
      </select>
      {isFetching 
        ? <div>Loading...</div> 
        : <p>{error}</p>
      }
      <div className="books-grid">
        {books.map((book, index) => (
          <a key={index} className="book-item" href={`/${book.title}`}>
            <img src={book.image_url} alt={book.title} />
            <div className="book-info">
              <h3>{book.title}</h3>
              <p>{book.newest_chapter.includes("Chapter") ? "" : "Chapter "}{book.newest_chapter}</p>
              <p>{book.genres.join(', ')}</p>
              <p>{book.status}</p>
            </div>
          </a>
        ))}
      </div>
    </div>
  );
};

export default Browse;
