import React, { useState, useEffect } from 'react';
import { useAuth } from '../components/AuthContext';
import './BookCard.scss';

const BookCard = ({ image_url, title, newest_chapter }) => {
  const { isLoggedIn } = useAuth();
  const img_placeholder = "https://via.placeholder.com/400x600/CCCCCC/FFFFFF?text=No+Image";
  const [imageUrl, setImageUrl] = useState(image_url || img_placeholder);

  useEffect(() => {
    setImageUrl(image_url || img_placeholder);
  }, [image_url]);

  const handleImageError = () => {
    setImageUrl(img_placeholder);
  };

  const CardContent = (
    <>
      <div className="image-container">
        <img
          src={imageUrl}
          alt={title}
          onError={handleImageError}
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