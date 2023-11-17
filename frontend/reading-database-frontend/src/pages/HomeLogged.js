import React from 'react';
import BookCarousel from '../components/BookCarousel.js';
import TopTenBooks from '../components/TopTenBooks.js';
import "slick-carousel/slick/slick.css"; 
import "slick-carousel/slick/slick-theme.css";

const HomeLogged = ({ books, lightMode }) => {
  // Ensure books is an array before calling .filter and .sort
  const isBooksArray = Array.isArray(books);

  const mangaBooks = isBooksArray ? books.filter(book => book.manga_type === "Manga") : [];
  const manhuaBooks = isBooksArray ? books.filter(book => book.manga_type === "Manhua") : [];
  const manhwaBooks = isBooksArray ? books.filter(book => book.manga_type === "Manhwa") : [];
  const recentlyUpdatedBooks = isBooksArray ? books.sort((a, b) => new Date(b.updated_on) - new Date(a.updated_on)) : [];

  // Make a copy of the books array and sort it by rating
  const sortedBooksByRating = isBooksArray ? [...books].sort((a, b) => parseFloat(b.rating) - parseFloat(a.rating)) : [];

  return (
    <div className="home">
      <main>
        {isBooksArray && <BookCarousel books={sortedBooksByRating.slice(0, 20)} />}
        <TopTenBooks title={"Recently Updated"} books={recentlyUpdatedBooks} />
        <TopTenBooks title={"Most Popular Manga This Month"} books={mangaBooks} />
        <TopTenBooks title={"Most Popular Manhua This Month"} books={manhuaBooks} />
        <TopTenBooks title={"Most Popular Manhwa This Month"} books={manhwaBooks} />
        <TopTenBooks title={"Most Popular Series"} books={sortedBooksByRating} />
      </main>
    </div>
  );
};

export default HomeLogged;
