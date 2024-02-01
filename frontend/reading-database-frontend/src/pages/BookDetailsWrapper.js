import React, { useState, useEffect } from 'react';
import { useParams } from 'react-router-dom';
import BookDetails from '../components/BookDetails'; 

const BookDetailsWrapper = () => {
  const { bookTitle } = useParams();
  const [bookDetails, setBookDetails] = useState(null);

  useEffect(() => {
    const fetchBookDetails = async () => {
      try {
        const response = await fetch(`/centralized_API_backend/api/book-details/${encodeURIComponent(bookTitle)}`);
        const data = await response.json();
        setBookDetails(data);
      } catch (error) {
        console.error('Error fetching book details:', error);
      }
    };
    fetchBookDetails();
  }, [bookTitle]);

  if (!bookDetails) {
    return <div>Loading...</div>;
  } else if (bookDetails?.message === "Book not found") {
    return <div>Book not found</div>;
  }

  return <BookDetails bookDetails={bookDetails} />;
};

export default BookDetailsWrapper;
