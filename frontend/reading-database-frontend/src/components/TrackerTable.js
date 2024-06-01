import React, { useState } from 'react';
import { useAuth } from './AuthContext';
import AddBookToTracker from './AddBookToTracker';
import FindBookForTracker from './FindBookForTracker';
import './TrackerTable.scss';

const TrackerTable = ({ books, fetchTrackingList, onBookEdited }) => {
  const [showEditModal, setShowEditModal] = useState(false);
  const [selectedBookForEdit, setSelectedBookForEdit] = useState(null);
  const [selectedBooks, setSelectedBooks] = useState({});
  const [selectAll, setSelectAll] = useState(false);

  const { user } = useAuth();
  
  const updateToMaxChapter = async (bookTitle, source) => {
    try {
      const response = await fetch(`/centralized_API_backend/api/update-to-max-chapter/`, {
        method: 'PUT',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          username: user.username,
          title: bookTitle,
          novel_source: source,
        }),
      });

      if (response.ok) {
        fetchTrackingList();
      } else {
        throw new Error(`HTTP error! status: ${response.status}`);
      }
    } catch (error) {
      console.error('Error updating to max chapter:', error);
    }
  };

  const updateSelectedToMaxChapter = async () => {
    const selectedBooksToUpdate = Object.keys(selectedBooks)
      .filter(title => selectedBooks[title])
      .map(title => {
        const book = books.find(book => book.title === title);
        return { title, source: book.novel_source };
      });

    // Perform fetch request for each book to update
    for (const book of selectedBooksToUpdate) {
      await updateToMaxChapter(book.title, book.source);
    }
  };

  const deleteBook = async (bookTitle, source) => {
    try {
      const response = await fetch(`/centralized_API_backend/api/delete-book-from-reading-list/`, {
        method: 'DELETE',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          username: user.username,
          title: bookTitle,
          novel_source: source,
        }),
      });

      if (response.ok) {
        fetchTrackingList();
      } else {
        throw new Error(`HTTP error! status: ${response.status}`);
      }
    } catch (error) {
      console.error('Error deleting book:', error);
    }
  };

  const deleteAllSelected = async () => {
    const selectedBooksToDelete = Object.keys(selectedBooks)
      .filter(title => selectedBooks[title])
      .map(title => {
        const book = books.find(book => book.title === title);
        return { title, source: book.novel_source };
      });

    // Perform fetch request for each book to delete
    for (const book of selectedBooksToDelete) {
      await deleteBook(book.title, book.source);
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

  const handleCloseEditModal = () => {
    setSelectedBookForEdit(null);
    setShowEditModal(false);
  };

  const handleSendBack = () => {
    setSelectedBookForEdit(null);
  };

  const handleSelectAll = () => {
    setSelectAll(!selectAll);
    setSelectedBooks(!selectAll ? books.reduce((acc, book) => ({...acc, [book.title]: true}), {}) : {});
  };

  const handleBookSelection = (title) => {
    setSelectedBooks(prevSelectedBooks => ({
      ...prevSelectedBooks,
      [title]: !prevSelectedBooks[title]
    }));
  };

  return (
    <div className="trackerTableContainer">
        <div className="tableHeader">
          {
          books && books.length === 0 
              ? <span className="headerText">No Books Found! Please add books to your tracker.</span>
              : <span className="headerText">Showing 1 to {books && books.length} of {books && books.length} results</span>
          }
          <button className="refreshButton" onClick={() => fetchTrackingList()}>Refresh</button>
          <button onClick={updateSelectedToMaxChapter}>Update Selected to Max Chapter</button>
          <button onClick={deleteAllSelected}>Delete All Selected</button>
          <button className="addButton" onClick={() => handleAddBook()}>+ Add Book</button>
        </div>
        <table className='trackerTable'>
          <thead>
            <tr>
                <th>
                  <input
                      type="checkbox"
                      checked={selectAll}
                      onChange={handleSelectAll}
                  />
                </th>
                <th>ID</th>
                <th>Title</th>
                <th>Source</th>
                <th>Last Chapter Read</th>
                <th>Latest Update</th>
                <th>Reading Status</th>
                <th>User Tag</th>
                <th>Actions</th>
            </tr>
          </thead>
          <tbody>
              {books && books.map((book, index) => (
                <tr key={index}>
                  <td>
                      <input
                      type="checkbox"
                      checked={!!selectedBooks[book.title]}
                      onChange={() => handleBookSelection(book.title)}
                      />
                  </td>
                  <td>{book.id}</td>
                  <td><a href={book.title} target="_blank" rel="noopener noreferrer">{book.title}</a></td>
                  <td>{book.novel_source}</td>
                  <td><a href={book.latest_read_chapter_link} target="_blank" rel="noopener noreferrer">{book.latest_read_chapter}</a></td>
                  <td><a href={book.newest_chapter_link} target="_blank" rel="noopener noreferrer">{book.newest_chapter}</a></td>
                  <td><span className={`status ${book.reading_status.toLowerCase()}`}>{book.reading_status}</span></td>
                  <td>{book.user_tag}</td>
                  <td>
                      {/* <button onClick={() => updateToMaxChapter(book.title, book.novel_source)}>Max</button> */}
                      <button onClick={() => handleEditBook(book)}>Edit</button>
                      {/* <button onClick={() => deleteBook(book.title, book.novel_source)}>Delete</button> */}
                  </td>
                </tr>
              ))}
          </tbody>
        </table>
        {showEditModal && !selectedBookForEdit && <FindBookForTracker onBookSelect={(book) => setSelectedBookForEdit(book)} onClose={handleCloseEditModal} />}
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
