import React, { useState, useEffect } from 'react';
import axios from 'axios';
import { BrowserRouter as Router, Route, Routes, useParams } from 'react-router-dom';
import Header from './components/Header'; 
import Footer from './components/Footer'; 
import Home from './pages/Home'; 
import Browse from './pages/Browse'; 
import NotFound from './pages/NotFound';
import BookDetailsWrapper from './pages/BookDetailsWrapper';
import TrackerPage from './pages/TrackerPage';

const App = () => {
  const [books, setBooks] = useState([]);
  const [lightMode, setLightMode] = useState(true);

  const API_ENDPOINT = 'http://127.0.0.1:8000';

  useEffect(() => {
    const fetchBooks = async () => {
      try {
        const response = await axios.get(`${API_ENDPOINT}/centralized_API_backend/api/all-novels/`);
        setBooks(response.data);
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
            <Route exact path="/" element={<Home books={books} lightMode={lightMode} />} />
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
