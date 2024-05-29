import React, { useState, useEffect } from 'react';
import { useParams } from 'react-router-dom';
import BookDetails from '../components/BookDetails'; 

const BookDetailsWrapper = () => {
  const { bookTitle } = useParams();
  const [bookDetails, setBookDetails] = useState(null);

  /*
   TODO: Update this to return ALL books with this name. Then, we'll have two (or more) buttons:
   - One button PER novel type (e.g. "Light Novel", "Manga", maybe "Anime" later ...)

   TODO: Update this URL to include the novel type (probably gonna be):
     /centralized_API_backend/api/book-details/<novel_type>/${encodeURIComponent(bookTitle)}
  */
  useEffect(() => {
    const fetchBookDetails = async () => {
      try {
        const response = await fetch(`/centralized_API_backend/api/book-details/${encodeURIComponent(bookTitle)}`);
        let data = await response.json();
        data.chapters = JSON.parse(data.chapters);
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
