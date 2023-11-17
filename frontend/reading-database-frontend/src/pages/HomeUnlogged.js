import React from 'react';
import BookCarousel from '../components/BookCarousel.js';
import Statistic from '../components/Statistic.js';
import "slick-carousel/slick/slick.css"; 
import "slick-carousel/slick/slick-theme.css";
import BannerDark from '../assets/BannerDark.png';
import BannerBoyBook from '../assets/BannerBoyBook.png';
import BannerSunset from '../assets/BannerSunset.png';
import './HomeUnlogged.scss';

const HomeUnlogged = ({ books, lightMode }) => {
  // Ensure books is an array before calling .filter and .sort
  const isBooksArray = Array.isArray(books);

  // Make a copy of the books array and sort it by rating
  const sortedBooksByRating = isBooksArray ? [...books].sort((a, b) => parseFloat(b.rating) - parseFloat(a.rating)) : [];

  return (
    <div className="home">
        {
            lightMode 
                ? <img className="banner" src={BannerBoyBook} alt="Home banner with a character reading"/>
                // ? <img className="banner" src={BannerDark} alt="Home banner with a character reading"/>
                : <img className="banner" src={BannerSunset} alt="Home banner with a character reading"/>
        }
        <main>
            {isBooksArray && <BookCarousel books={sortedBooksByRating.slice(0, 20)} />}
            <Statistic label="Total Number of Books" value={isBooksArray ? books.length : 0} />
        </main>
    </div>
  );
};

export default HomeUnlogged;
