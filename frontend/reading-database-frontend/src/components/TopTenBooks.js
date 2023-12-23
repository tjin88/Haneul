import React from 'react';
import './TopTenBooks.scss';

const TopTenBooks = ({ title, books }) => {
  return (
    <div className="top-six-books-container py-6 sm:px-2 lg:mx-auto lg:px-1 lg:max-w-7xl 5xl:max-w-10xl">
      <div className="mb-8 px-4 flex items-center justify-between">
        <h2 id="collection-heading">{title}</h2>
        <a href="/browse" className="see-all">See All {books.length} Books →</a>
      </div>
      <div className="books-slider relative">
        <div className="books-list flex gap-4 overflow-x-auto">
          {books.slice(0, 11).map((book, index) => (
            <a href={book.link} key={index} className="book-card">
              <img src={book.image_url} alt={book.title} className="book-cover rounded-lg" />
              {/* TODO: Make these clickable --> Should go to the website's page for that book */}
              <div className="book-info">
                <p className="book-title">{book.title}</p>
                <p className="tracking-info">Rating: {book.rating}</p>
              </div>
            </a>
          ))}
        </div>
      </div>
    </div>
  );
};

export default TopTenBooks;
