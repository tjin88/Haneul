import React from 'react';
import './TrackerTable.scss';

const TrackerTable = ({ books }) => {
  return (
    <div className="trackerTableContainer">
      <table className='trackerTable'>
        <thead>
          <tr>
            <th>Title</th>
            <th>Latest Read Chapter</th>
            <th>Reading Status</th>
            <th>User Tag</th>
          </tr>
        </thead>
        <tbody>
          {books.map((book, index) => (
            <tr key={index}>
              <td>{book.title}</td>
              <td>{book.latest_read_chapter}</td>
              <td>{book.reading_status}</td>
              <td>{book.user_tag}</td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
};

export default TrackerTable;
