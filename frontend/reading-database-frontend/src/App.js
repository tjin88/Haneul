import React, { useState, useEffect } from 'react';
import axios from 'axios';
import { BrowserRouter as Router, Route, Routes, useParams } from 'react-router-dom';
// import { useGoogleOneTapLogin } from '@react-oauth/google';
import Header from './components/Header'; 
import Footer from './components/Footer'; 
import HomeLogged from './pages/HomeLogged'; 
import HomeUnlogged from './pages/HomeUnlogged'; 
import Browse from './pages/Browse'; 
import NotFound from './pages/NotFound';
import BookDetailsWrapper from './components/BookDetailsWrapper';
import TrackerPage from './pages/TrackerPage';
import { useAuth } from './components/AuthContext';

const App = () => {
  const [books, setBooks] = useState([]);
  const [lightMode, setLightMode] = useState(true);
  const { isLoggedIn } = useAuth();

  const API_ENDPOINT = 'http://127.0.0.1:8000';

  // useGoogleOneTapLogin({
  //   onSuccess: tokenResponse => {
  //     axios.get(`https://www.googleapis.com/oauth2/v3/tokeninfo?id_token=${tokenResponse.credential}`)
  //       .then(response => {
  //         const profile = response.data;
  //         setUser({
  //           id: profile.sub,
  //           email: profile.email,
  //           fullName: profile.name,
  //           givenName: profile.given_name,
  //           profileImage: profile.picture
  //         });
  //         console.log(`Sucessfully logged in. User: ${user}`)
  //       })
  //       .catch(error => console.error('Error fetching Google profile:', error));
  //   },
  //   onError: error => console.error('Google login failed:', error)
  // });

  useEffect(() => {
    const fetchBooks = async () => {
      try {
        const response = await axios.get(`${API_ENDPOINT}/centralized_API_backend/api/manga/`);
        setBooks(response.data);
      } catch (error) {
        console.error('Error fetching books:', error);
      }
    };
    fetchBooks();
  }, []);

  return (
      <Router>
        <Header/>
          <Routes>
            {!isLoggedIn && <Route exact path="/" element={<HomeUnlogged books={books} lightMode={lightMode} />} />}
            {isLoggedIn && <Route path="/" element={<HomeLogged books={books} lightMode={lightMode} />} />}
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
