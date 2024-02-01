import React, { useState, useEffect } from 'react';
import { BrowserRouter as Router, Route, Routes } from 'react-router-dom';
import Header from './components/Header'; 
import Footer from './components/Footer'; 
import Home from './pages/Home'; 
import Browse from './pages/Browse'; 
import NotFound from './pages/NotFound';
import BookDetailsWrapper from './pages/BookDetailsWrapper';
import TrackerPage from './pages/TrackerPage';

const App = () => {
  const [books, setBooks] = useState([]);
  const [totalNumberOfBooks, setTotalNumberOfBooks] = useState(1478);
  const [lightMode, setLightMode] = useState(true);

  useEffect(() => {
    const fetchBooks = async () => {
      try {
        // const response = await fetch(`/centralized_API_backend/api/all-novels/`);
        const response = await fetch(`/centralized_API_backend/api/home-novels/`);
        if (!response.ok) {
          throw new Error(`HTTP error! status: ${response.status}`);
        }
        const data = await response.json();
        setBooks(data.books);
        setTotalNumberOfBooks(data.numberOfBooks);
      } catch (error) {
        console.error('Error fetching books:', error);
      }
    };
    fetchBooks();
  }, []);

  return (
      <Router>
        <Header isLightMode={lightMode} setLightMode={setLightMode}/>
          <Routes>
            <Route exact path="/" element={<Home books={books} totalNumberOfBooks={totalNumberOfBooks} lightMode={lightMode} />} />
            <Route path="/browse" element={<Browse books={books} lightMode={lightMode} />} />
            <Route path="/track" element={<TrackerPage lightMode={lightMode} />} />
            <Route path="/:bookTitle" element={<BookDetailsWrapper books={books} />} />
            <Route path="*" element={<NotFound lightMode={lightMode} />} />
          </Routes>
        <Footer/>
      </Router>
  );
};

export default App;
