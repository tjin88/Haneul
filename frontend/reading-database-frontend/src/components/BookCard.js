import React from 'react';
import { useAuth } from '../components/AuthContext';
import { LazyLoadImage } from 'react-lazy-load-image-component';
import loading from '../assets/ManBlackWhite.png';  // TODO: Find a good background photo!
import 'react-lazy-load-image-component/src/effects/blur.css';
import './BookCard.scss';

const BookCard = ({ image_url, title, newest_chapter }) => {
  const { isLoggedIn } = useAuth();

  const CardContent = (
    <>
      <div className="image-container">
        <LazyLoadImage
          src={image_url}
          alt={title}
          className="book-image"
          effect="blur"
          placeholderSrc={loading}
        />
      </div>
      <div className="book-info">
        <span className="title">{title}</span>
        <br />
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
