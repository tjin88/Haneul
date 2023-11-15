import React, { useState, useEffect } from 'react';
import axios from 'axios';
import { BrowserRouter as Router, Route, Routes } from 'react-router-dom';
import Header from './components/Header'; 
import Footer from './components/Footer'; 
import Home from './pages/Home'; 
import Browse from './pages/Browse'; 
import NotFound from './pages/NotFound';

const App = () => {
    const [books, setBooks] = useState([]);
    const [login, setLogin] = useState(false);

    useEffect(() => {
        const fetchBooks = async () => {
        try {
            const response = await axios.get('http://127.0.0.1:8000/centralized_API_backend/api/manga/');
            setBooks(response.data);
        } catch (error) {
            console.error('Error fetching books:', error);
        }
        };

        fetchBooks();
    }, []);


    // const handleLogin = () => {
    //     return null;
    // };

    const handleRegister = () => {
        return null;
    };
    
  return (
    <Router>
      <Header login={login} setLogin={() => setLogin(!login)} onRegister={handleRegister} />
      <Routes>
        <Route exact path="/" element={<Home books={books} />} />
        <Route path="/browse" element={<Browse books={books} />} />
        
        {/* This will catch all other routes that haven't matched */}
        <Route path="*" element={<NotFound/>} />
      </Routes>
      <Footer/>
    </Router>
  );
};

export default App;
