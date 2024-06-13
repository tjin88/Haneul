import React, { useState, useEffect } from 'react';
import { useParams } from 'react-router-dom';
import BookDetails from '../components/BookDetails';
import Select from 'react-select';
import './BookDetailsWrapper.scss';

const BookDetailsWrapper = () => {
  const { bookTitle } = useParams();
  const [books, setBooks] = useState({});
  const [selectedBook, setSelectedBook] = useState(null);
  const [novelTypes, setNovelTypes] = useState([]);
  const [error, setError] = useState(null);

  useEffect(() => {
    const fetchBooks = async () => {
      try {
        const response = await fetch(`${process.env.REACT_APP_API_URL}/centralized_API_backend/api/book-details/${encodeURIComponent(bookTitle)}`);
        let data = await response.json();
        if (data.message === 'Book not found') {
          setError('Book not found');
          return;
        }
        for (let type in data) {
          data[type].forEach(book => {
            if (book.chapters) {
              book.chapters = JSON.parse(book.chapters);
            }
          });
        }
        setBooks(data);
        setNovelTypes(Object.keys(data));
        const initialSelectedBook = data[Object.keys(data)[0]][0];
        setSelectedBook(initialSelectedBook);
      } catch (error) {
        console.error('Error fetching book details:', error);
        setError('Error fetching book details');
      }
    };
    fetchBooks();
  }, [bookTitle]);

  if (error) {
    return <div>{error}</div>;
  }

  if (Object.keys(books).length === 0) {
    return <div>Loading...</div>;
  }

  const handleSelectBook = (selectedOption) => {
    const [type, index] = selectedOption.value.split('-');
    const selected = books[type][index];
    setSelectedBook(selected); // Set the selected book for display
  };

  const options = novelTypes.map(type => ({
    label: type,
    options: books[type].map((book, index) => ({
      value: `${type}-${index}`,
      label: `${book.novel_source} (${type})`,
      type: type,
    })),
  }));

  const selectedOption = selectedBook
    ? {
        value: `${selectedBook.novel_type}-${books[selectedBook.novel_type].indexOf(selectedBook)}`,
        label: `${selectedBook.novel_source} (${selectedBook.novel_type})`,
        type: selectedBook.novel_type,
      }
    : null;

  return (
    <div className="book-details-wrapper">
      <div className="dropdown-container">
        <Select
          className="novel-select"
          options={options}
          value={selectedOption}
          onChange={handleSelectBook}
        />
      </div>
      {selectedBook && <BookDetails bookDetails={selectedBook} />}
    </div>
  );
};

export default BookDetailsWrapper;
