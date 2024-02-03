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
  const [lightMode, setLightMode] = useState(true);

  return (
      <Router>
        <Header isLightMode={lightMode} setLightMode={setLightMode}/>
          <Routes>
            <Route exact path="/" element={<Home lightMode={lightMode} />} />
            <Route path="/browse" element={<Browse lightMode={lightMode} />} />
            <Route path="/track" element={<TrackerPage lightMode={lightMode} />} />
            <Route path="/:bookTitle" element={<BookDetailsWrapper />} />
            <Route path="*" element={<NotFound lightMode={lightMode} />} />
          </Routes>
        <Footer/>
      </Router>
  );
};

export default App;
