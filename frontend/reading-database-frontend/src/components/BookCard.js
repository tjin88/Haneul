import React from 'react';
import { useAuth } from '../components/AuthContext';
import './BookCard.scss';

const BookCard = ({ image_url, title, newest_chapter }) => {
  const { isLoggedIn } = useAuth();

  const CardContent = (
    <>
      <div className="image-container">
        <img
          loading="lazy"
          src={image_url}
          alt={title}
          className="book-image"
        />
      </div>
      <div className="book-info">
        <span className="title">{title}</span>
        <span className="chapters">{newest_chapter && newest_chapter.includes("Chapter") ? "" : "Chapter "}{newest_chapter}</span>
      </div>
    </>
  );

  return (
    isLoggedIn 
      ? <a className="book-card" href={`/${encodeURIComponent(title)}`}>{CardContent}</a>
      : <div className="book-card">{CardContent}</div>
  );
};

export default BookCard;