import React from 'react';
import './TrackerTable.scss';

const TrackerTable = ({ books }) => {
  return (
    <div className="trackerTableContainer">
      <div className="tableHeader">
        {
          books.length === 0 
            ? <span className="headerText">No Books Found! Please add books to your tracker.</span>
            : <span className="headerText">Showing 1 to {books.length} of {books.length} results</span>
        }
        <button className="refreshButton">Refresh (To Be Implemented)</button>
        <button className="addButton">+ Add Book (To Be Implemented)</button>
      </div>
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
              <td><a href={book.title} target="_blank" rel="noopener noreferrer">{book.title}</a></td>
              <td><a href={book.chapter_link} target="_blank" rel="noopener noreferrer">{book.latest_read_chapter}</a></td>
              <td><span className={`status ${book.reading_status.toLowerCase()}`}>{book.reading_status}</span></td>
              <td>{book.user_tag}</td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
};

export default TrackerTable;



// import React from 'react';
// import './TrackerTable.scss';

// const TrackerTable = ({ books }) => {
//   return (
//     <div className="trackerTableContainer">
//       <table className='trackerTable'>
//         <thead>
//           <tr>
//             <th>Title</th>
//             <th>Latest Read Chapter</th>
//             <th>Reading Status</th>
//             <th>User Tag</th>
//           </tr>
//         </thead>
//         <tbody>
//           {books.map((book, index) => (
//             <tr key={index}>
//               <td>{book.title}</td>
//               <td>{book.latest_read_chapter}</td>
//               <td>{book.reading_status}</td>
//               <td>{book.user_tag}</td>
//             </tr>
//           ))}
//         </tbody>
//       </table>
//     </div>
//   );
// };

// export default TrackerTable;
