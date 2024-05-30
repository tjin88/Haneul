import React from 'react';
import BookCarousel from './BookCarousel';
import './TopTenBooks.scss';

const TopTenBooks = ({ title, books, numBooks }) => {
  const numberOfBooks = numBooks ? numBooks : books.length
  return (
    <div className="top-six-books-container py-6 sm:px-2 lg:mx-auto lg:px-1 lg:max-w-7xl 5xl:max-w-10xl">
      <div className="mb-8 px-4 flex items-center justify-between">
        <h2 id="collection-heading">{title}</h2>
        <a href="/browse" className="see-all">See {numberOfBooks <= 1 ? `${numberOfBooks} Book` : `All ${numberOfBooks} Books`} →</a>
      </div>
      <BookCarousel books={books} />
    </div>
  );
};

export default TopTenBooks;
