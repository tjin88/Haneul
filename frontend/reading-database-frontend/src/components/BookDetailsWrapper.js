import React from 'react';
import { useParams } from 'react-router-dom';
import BookDetails from '../pages/BookDetails'; 

const BookDetailsWrapper = ({ books }) => {
  const { bookTitle } = useParams();
  
  // Assuming the book titles are decoded in the URL
  const decodedTitle = decodeURIComponent(bookTitle);
  const bookDetails = books.find(book => book.title === decodedTitle);

  // Check if bookDetails is found
  if (!bookDetails) {
    return <div>Book not found</div>;
  }

  return <BookDetails bookDetails={bookDetails} />;
};

export default BookDetailsWrapper;
