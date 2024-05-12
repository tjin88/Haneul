import React from 'react';
import { useAuth } from '../components/AuthContext';
import './BookCard.scss';

const BookCard = ({ image_url, title, newest_chapter }) => {
  const { isLoggedIn } = useAuth();

  return (
    <>
      { isLoggedIn 
        ?
          <a className="book-card" href={`/${encodeURIComponent(title)}`}>
            <div className="image-container">
              <img src={image_url} alt={title} className="book-image" />
            </div>
            <div className="book-info">
              <span className="title">{title}</span>
              <br />
              <span className="chapters">{newest_chapter.includes("Chapter") ? "" : "Chapter "}{newest_chapter}</span>
            </div>
          </a>
        : <div className="book-card">
            <div className="image-container">
              <img src={image_url} alt={title} className="book-image" />
            </div>
            <div className="book-info">
              <span className="title">{title}</span>
              <br />
              <span className="chapters">{newest_chapter.includes("Chapter") ? "" : "Chapter "}{newest_chapter}</span>
            </div>
          </div>
      }
    </>
  );
};

export default BookCard;
