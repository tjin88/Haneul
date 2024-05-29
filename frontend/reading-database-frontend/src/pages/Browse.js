import React, { useState, useEffect } from 'react';
import { useInView } from 'react-intersection-observer';
import BookCard from '../components/BookCard';
import './Browse.scss';

const Browse = ({ lightMode }) => {
  const [searchTerm, setSearchTerm] = useState('');
  const [sortType, setSortType] = useState('');
  const [genreFilter, setGenreFilter] = useState('');
  const [books, setBooks] = useState([]);
  const [isFetching, setIsFetching] = useState(false);
  const [error, setError] = useState('');
  const [page, setPage] = useState(1);
  const [totalCount, setTotalCount] = useState(0);

  const { ref, inView } = useInView({
    threshold: 0,
  });

  useEffect(() => {
    const fetchData = async () => {
      setIsFetching(true);
      const title = encodeURIComponent(searchTerm);
      const genre = encodeURIComponent(genreFilter);
      const response = await fetch(`/centralized_API_backend/api/all-novels/browse?title=${title}&genre=${genre}&page=${page}&sortType=${sortType}`);
      const data = await response.json();
      if (page === 1) {
        setBooks(data.results);
      } else {
        setBooks(prevBooks => [...prevBooks, ...data.results]);
      }
      if (data.results.length === 0 && page === 1) {
        setError('No books matching the search criteria found!');
      } else {
        setError('');
      }
      setTotalCount(data.total_count);
      setIsFetching(false);
    };

    const debounceFetchData = setTimeout(() => {
      if (searchTerm.length >= 2 || genreFilter) {
        setError('');
        fetchData();
      } else if (sortType !== '') {
        setBooks([]);
        setError('Please search (with 2 or more characters) or add a genre!');
      } else if (searchTerm.length > 0 && searchTerm.length < 2) {
        setBooks([]);
        setError('Please enter a search with 2 or more characters!');
      } else {
        setError('');
      }
    }, 500); // 500ms delay

    return () => clearTimeout(debounceFetchData); 
  }, [searchTerm, genreFilter, sortType, page]);

  useEffect(() => {
    if (inView && !isFetching && books.length < totalCount) {
      setPage(prevPage => prevPage + 1);
    }
  }, [inView, isFetching, books.length, totalCount]);

  const handleSearchChange = (e) => {
    setSearchTerm(e.target.value);
    setPage(1);
  };

  const handleGenreChange = (e) => {
    setGenreFilter(e.target.value);
    setPage(1);
  };

  return (
    <div className="browse">
      <input
        type="text"
        placeholder="Search by title (2 characters minimum)"
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
        {books && books.map((book, index) => (
          <BookCard key={index} {...book} />
        ))}
      </div>
      <div ref={ref} style={{ height: '1px' }}></div>
    </div>
  );
};

export default Browse;
