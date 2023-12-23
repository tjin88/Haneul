import React, { useState } from 'react';
import AddBookToTracker from '../components/AddBookToTracker';
import './BookDetails.scss';

const BookDetails = ({ bookDetails }) => {
  const [showModal, setShowModal] = useState(false);

  if (!bookDetails) {
    return <div>Loading...</div>;
  }

  const handleCloseModal = () => {
    setShowModal(false);
  };

  return (
    <div className="book-details">
      <div className="book-cover">
        <img src={bookDetails.image_url} alt={bookDetails.title} />
        <button className="add-dashboard-button" onClick={() => setShowModal(true)}>Add to your Dashboard</button>
        {showModal && <AddBookToTracker givenBook={bookDetails} sendBack={handleCloseModal} onClose={handleCloseModal} />}
      </div>
      <div className="book-content">
        <h1 className="book-title">{bookDetails.title}</h1>
        <div className="book-genres">
          {bookDetails.genres.map((genre, index) => (
            <span key={index} className="genre">{genre}</span>
          ))}
        </div>
        <div className="book-info">
          <p className="type"><strong>Source:</strong> {bookDetails.novel_source}</p>
          <p className="users-tracking"><strong>Followers:</strong> {bookDetails.followers}</p>
          <p className="chapters-available"><strong>Chapters Available:</strong> {Object.keys(bookDetails.chapters).length}</p>
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
                        {Object.entries(bookDetails.chapters).map(([chapter, link], index) => (
                            <tr key={index}>
                            <td>{chapter}</td>
                            <td><a href={link} target="_blank" rel="noopener noreferrer">Read</a></td>
                            </tr>
                        ))}
                    </tbody>
                </table>
            </div>
        </div>
        {/* Add additional sections as needed */}
      </div>
    </div>
  );
};

export default BookDetails;
