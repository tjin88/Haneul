import React, { useState, useEffect } from 'react';
import { useInView } from 'react-intersection-observer';
import Select from 'react-select';
import makeAnimated from 'react-select/animated';
import BookCard from '../components/BookCard';
import './Browse.scss';

const Browse = ({ lightMode }) => {
  const [searchTerm, setSearchTerm] = useState('');
  const [sortType, setSortType] = useState([]);
  const [genreFilter, setGenreFilter] = useState([]);
  const [genres, setGenres] = useState([]);
  const [books, setBooks] = useState([]);
  const [isFetching, setIsFetching] = useState(false);
  const [error, setError] = useState('');
  const [page, setPage] = useState(1);
  const [totalCount, setTotalCount] = useState(0);
  const [hasMoreBooks, setHasMoreBooks] = useState(true);
  const animatedComponents = makeAnimated();

  const { ref, inView } = useInView({
    threshold: 0,
  });

  useEffect(() => {
    const fetchGenres = async () => {
      try {
        const response = await fetch(`/centralized_API_backend/api/genres`);
        const data = await response.json();
        setGenres(data.map(genre => ({ value: genre, label: genre })));
      } catch (error) {
        console.error('Error fetching genres:', error);
      }
    };

    fetchGenres();
  }, []);

  useEffect(() => {
    const fetchData = async () => {
      if (isFetching || !hasMoreBooks) return;

      setIsFetching(true);
      const title = encodeURIComponent(searchTerm).replace("'", "’");
      const genre = encodeURIComponent(genreFilter.map(g => g.value).join(','));
      const sort = encodeURIComponent(sortType.map(g => g.value).join(','));
      const response = await fetch(`/centralized_API_backend/api/all-novels/browse?title=${title}&genre=${genre}&page=${page}&sortType=${sort}`);
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
      setHasMoreBooks(data.results.length > 0);
      setIsFetching(false);
    };

    const debounceFetchData = setTimeout(() => {
      if (searchTerm.length >= 2 || genreFilter.length > 0 || sortType.length > 0) {
        setError('');
        fetchData();
      } else if (searchTerm.length > 0 && searchTerm.length < 2) {
        setBooks([]);
        setError('Please enter a search with 2 or more characters!');
      } else {
        setError('');
      }
    }, 300); // 300ms delay

    return () => clearTimeout(debounceFetchData);
  }, [searchTerm, genreFilter, sortType, page]);

  useEffect(() => {
    if (inView && !isFetching && books.length < totalCount && hasMoreBooks) {
      setPage(prevPage => prevPage + 1);
    }
  }, [inView, isFetching, books.length, totalCount, hasMoreBooks]);

  const handleSearchChange = (e) => {
    setPage(1);
    // setBooks([]);
    setHasMoreBooks(true);
    setSearchTerm(e.target.value);
  };

  const handleGenreChange = (selectedOptions) => {
    setPage(1);
    // setBooks([]);
    setHasMoreBooks(true);
    setGenreFilter(selectedOptions || []);
  };

  const handleSortChange = (selectedOption) => {
    setPage(1);
    // setBooks([]);
    setHasMoreBooks(true);
    setSortType(selectedOption);
  };

  const sortOptions = [
    { value: 'manga', label: 'Manga' },
    { value: 'manhua', label: 'Manhua' },
    { value: 'manhwa', label: 'Manhwa' },
    { value: 'light_novel', label: 'Light Novel' },
    { value: 'rating', label: 'Rating' },
    { value: 'updated', label: 'Recently Updated' },
    { value: 'followers', label: 'Most Followers' },
  ];

  return (
    <div className="browse">
      <input
        type="text"
        placeholder="Search by title (2 characters minimum)"
        value={searchTerm}
        onChange={handleSearchChange}
        className="search-input"
      />
      <Select
        isMulti
        components={animatedComponents}
        value={genreFilter}
        onChange={handleGenreChange}
        options={genres}
        className="select"
        placeholder="Select genres..."
      />
      <Select
        isMulti
        components={animatedComponents}
        value={sortType}
        onChange={handleSortChange}
        options={sortOptions}
        className="select"
        placeholder="Sort by..."
      />
      {isFetching ? <div className="spinner">Loading...</div> : <p>{error}</p>}
      <div className="books-grid">
        {books && books.map((book, index) => (
          <BookCard key={index} image_url={book.image_url} title={book.title} newest_chapter={book.newest_chapter} />
        ))}
      </div>
      <div ref={ref} style={{ height: '1px' }}></div>
    </div>
  );
};

export default Browse;