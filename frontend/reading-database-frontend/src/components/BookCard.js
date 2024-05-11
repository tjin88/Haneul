import React from 'react';
import './BookCard.scss';

const BookCard = ({ image_url, title, newest_chapter }) => {
  return (
    <a className="book-card" href={`/${encodeURIComponent(title)}`}>
      <div className="image-container">
        <img src={image_url} alt={title} className="book-image" />
      </div>
      <div className="book-info">
        <span className="title">{title}</span>
        <br />
        <span className="chapters">Chapter {newest_chapter}</span>
      </div>
    </a>
  );
};

export default BookCard;
