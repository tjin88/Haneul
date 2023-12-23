import React, { useState } from 'react';
import axios from 'axios';
import { useAuth } from './AuthContext';
import AddBookToTracker from './AddBookToTracker';
import FindBookForTracker from './FindBookForTracker';
import './TrackerTable.scss';

const TrackerTable = ({ books, fetchTrackingList, onBookEdited }) => {
  const [showEditModal, setShowEditModal] = useState(false);
  const [selectedBookForEdit, setSelectedBookForEdit] = useState(null);
  
  const { user } = useAuth();

  const API_ENDPOINT = 'http://127.0.0.1:8000';

  const updateToMaxChapter = async (bookTitle, source) => {
    try {
      const response = await axios.put(`${API_ENDPOINT}/centralized_API_backend/api/update-to-max-chapter/`, {
        username: user.username,
        title: bookTitle,
        novel_source: source
      });

      if (response.status === 200) {
        fetchTrackingList();
      }
    } catch (error) {
      console.error('Error updating to max chapter:', error);
    }
  };

  const deleteBook = async (bookTitle, source) => {
    try {
      const response = await axios.delete(`${API_ENDPOINT}/centralized_API_backend/api/delete-book-from-reading-list/`, {
        data: {
          username: user.username,
          title: bookTitle,
          novel_source: source
        },
      });
      if (response.status === 200) {
        fetchTrackingList();
      }
    } catch (error) {
      console.error('Error deleting book:', error);
    }
  };

  const handleEditBook = (book) => {
    setSelectedBookForEdit(book);
    setShowEditModal(true);
  };

  const handleAddBook = () => {
    setSelectedBookForEdit(null);
    setShowEditModal(true);
  };

  const handleSelectBook = (book) => {
    setSelectedBookForEdit(book);
  };

  const handleCloseEditModal = () => {
    setSelectedBookForEdit(null);
    setShowEditModal(false);
  };

  const handleSendBack = () => {
    setSelectedBookForEdit(null);
  };

  return (
    <div className="trackerTableContainer">
      <div className="tableHeader">
        {
          books.length === 0 
            ? <span className="headerText">No Books Found! Please add books to your tracker.</span>
            : <span className="headerText">Showing 1 to {books.length} of {books.length} results</span>
        }
        <button className="refreshButton" onClick={() => fetchTrackingList()}>Refresh</button>
        <button className="addButton" onClick={() => handleAddBook()}>+ Add Book</button>
      </div>
      <table className='trackerTable'>
        <thead>
          <tr>
            <th>Title</th>
            <th>Source</th>
            <th>Latest Read Chapter</th>
            <th>Reading Status</th>
            <th>User Tag</th>
            <th>Edit</th>
          </tr>
        </thead>
        <tbody>
          {books.map((book, index) => (
            <tr key={index}>
              <td><a href={book.title} target="_blank" rel="noopener noreferrer">{book.title}</a></td>
              <td>{book.novel_source}</td>
              <td><a href={book.chapter_link} target="_blank" rel="noopener noreferrer">{book.latest_read_chapter}</a></td>
              <td><span className={`status ${book.reading_status.toLowerCase()}`}>{book.reading_status}</span></td>
              <td>{book.user_tag}</td>
              <td>
                <button onClick={() => updateToMaxChapter(book.title, book.novel_source)}>Max</button>
                <button onClick={() => handleEditBook(book)}>Edit</button>
                <button onClick={() => deleteBook(book.title, book.novel_source)}>Delete</button>
              </td>
            </tr>
          ))}
        </tbody>
      </table>
      {showEditModal && !selectedBookForEdit && <FindBookForTracker onBookSelect={handleSelectBook} onClose={handleCloseEditModal} />}
      {showEditModal && selectedBookForEdit && (
        <AddBookToTracker
          onBookAdded={onBookEdited}
          onClose={handleCloseEditModal}
          sendBack={handleSendBack}
          givenBook={selectedBookForEdit}
        />
      )}
    </div>
  );
};

export default TrackerTable;
