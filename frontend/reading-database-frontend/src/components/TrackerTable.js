import React from 'react';
import axios from 'axios';
import { useAuth } from './AuthContext';
import './TrackerTable.scss';

const TrackerTable = ({ books, fetchTrackingList }) => {
  const { user } = useAuth();

  const API_ENDPOINT = 'http://127.0.0.1:8000';

  const updateToMaxChapter = async (bookTitle) => {
    try {
      const response = await axios.put(`${API_ENDPOINT}/centralized_API_backend/api/update-to-max-chapter/`, {
        username: user.username,
        title: bookTitle,
      });

      if (response.status === 200) {
        fetchTrackingList();
      }
    } catch (error) {
      console.error('Error updating to max chapter:', error);
    }
  };

  const deleteBook = async (bookTitle) => {
    try {
      const response = await axios.delete(`${API_ENDPOINT}/centralized_API_backend/api/delete-book-from-reading-list/`, {
        data: {
          username: user.username,
          title: bookTitle
        },
      });
      if (response.status === 200) {
        fetchTrackingList();
      }
    } catch (error) {
      console.error('Error deleting book:', error);
    }
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
        <button className="addButton">+ Add Book (To Be Implemented)</button>
      </div>
      <table className='trackerTable'>
        <thead>
          <tr>
            <th>Title</th>
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
              <td><a href={book.chapter_link} target="_blank" rel="noopener noreferrer">{book.latest_read_chapter}</a></td>
              <td><span className={`status ${book.reading_status.toLowerCase()}`}>{book.reading_status}</span></td>
              <td>{book.user_tag}</td>
              <td>
                <button onClick={() => updateToMaxChapter(book.title)}>Max</button>
                {/* EDIT icon */}
                <button onClick={() => deleteBook(book.title)}>Delete</button>
              </td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
};

export default TrackerTable;
