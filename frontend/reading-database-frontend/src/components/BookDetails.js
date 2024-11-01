import React, { useState } from 'react';
import AddBookToTracker from './AddBookToTracker';
import Image_Placeholder from '../assets/placeholder.png';
import './BookDetails.scss';

const BookDetails = ({ bookDetails }) => {
  const [imageUrl, setImageUrl] = useState(bookDetails.image_url || Image_Placeholder);
  const [showModal, setShowModal] = useState(false);
  const last_updated = new Date(bookDetails.updated_on);

  if (!bookDetails) {
    return <div>Loading...</div>;
  }

  const handleCloseModal = () => {
    setShowModal(false);
  };

  const handleImageError = () => {
    setImageUrl(Image_Placeholder);
  };

  // Check if chapters are in string format and parse if necessary
  let chapters;
  try {
    chapters = typeof bookDetails.chapters === 'string' ? JSON.parse(bookDetails.chapters) : bookDetails.chapters;
  } catch (error) {
    console.error('Error parsing chapters:', error);
    chapters = {};
  }

  return (
    <div className="book-details">
      <div className="book-cover">
        <img src={imageUrl} alt={bookDetails.title} onError={handleImageError} />
        <button className="add-dashboard-button" onClick={() => setShowModal(true)}>Add to your Dashboard</button>
        {showModal && <AddBookToTracker givenBook={bookDetails} sendBack={handleCloseModal} onClose={handleCloseModal} />}
      </div>
      <div className="book-content">
        <h1 className="book-title">{bookDetails.title}</h1>
        <div className="book-genres">
          {bookDetails.genres && bookDetails.genres.length > 0 ? (
            bookDetails.genres.map((genre, index) => (
              <span key={index} className="genre">{genre}</span>
            ))
          ) : (
            <span className="no-genres">No genres available</span>
          )}
        </div>
        <div className="book-info">
          <p className="novel_source"><strong>Source:</strong> {bookDetails.novel_source}</p>
          <p className="novel_author"><strong>Author:</strong> {bookDetails.author}</p>
          <p className="users-tracking"><strong>Followers:</strong> {bookDetails.followers}</p>
          <p className="chapters-available"><strong>Chapters Available:</strong> {Object.keys(chapters).length}</p>
          <p className="novel_last_updated"><strong>Last Updated On:</strong> {last_updated.toString()}</p>
          <p className="novel_status"><strong>Status:</strong> {bookDetails.status}</p>
        </div>
        <div className="book-synopsis">
          <h2>Synopsis</h2>
          <p>{bookDetails.synopsis}</p>
        </div>
        <div className="book-chapters">
          <h2>Chapters</h2>
          <div className="chapter-table-container">
            <table className="chapter-table">
              <thead>
                <tr>
                  <th>Chapter</th>
                  <th>Link</th>
                </tr>
              </thead>
              <tbody>
                {chapters && Object.entries(chapters).map(([chapter, link], index) => (
                  <tr key={index}>
                    <td>{chapter}</td>
                    <td><a href={link} target="_blank" rel="noopener noreferrer">Read</a></td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>
      </div>
    </div>
  );
};

export default BookDetails;
