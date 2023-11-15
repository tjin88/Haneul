import React from 'react';
import './TopTenBooks.scss';

const TopTenBooks = ({ title, books }) => {
  return (
    <div className="top-six-books-container py-6 sm:px-2 lg:mx-auto lg:px-1 lg:max-w-7xl 5xl:max-w-10xl">
      <div className="mb-8 px-4 flex items-center justify-between">
        <h2 id="collection-heading">{title}</h2>
        {/* <a href="/search?sort=newest+desc" className="see-all">See All {books.length} Books →</a> */}
        <a href="/browse" className="see-all">See All {books.length} Books →</a>
      </div>
      <div className="books-slider relative">
        <div className="books-list flex gap-4 overflow-x-auto">
          {books.slice(0, 11).map((book, index) => (
            <div key={index} className="book-card">
              <a href={book.link}>
                <img src={book.image_url} alt={book.title} className="book-cover rounded-lg" />
              </a>
              <div className="book-info">
                <a href={book.link}>
                  <span className="book-title">{book.title}</span>
                </a>
                <p className="tracking-info">Rating: {book.rating}</p>
                {/* <p className="tracking-info">0 Users Tracking</p> */}
              </div>
            </div>
          ))}
        </div>
      </div>
    </div>
  );
};

export default TopTenBooks;
