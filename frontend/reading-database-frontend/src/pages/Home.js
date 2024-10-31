import React, { useState, useEffect } from 'react';
import Welcome from '../components/Welcome.js';
import PreRelease from '../components/PreRelease.js';
import BookCarousel from '../components/BookCarousel.js';
import TopTenBooks from '../components/TopTenBooks.js';
import Statistic from '../components/Statistic.js';
import CookieNotice from '../components/CookieNotice.js';
import "slick-carousel/slick/slick.css"; 
import "slick-carousel/slick/slick-theme.css";
// import BannerDark from '../assets/BannerDark.png';
import BannerBoyVideo from '../assets/BannerBoyVideo.mp4';
import BannerBoyBook from '../assets/BannerBoyBook.png';
// import BannerSunset from '../assets/BannerSunset.png';
import { useAuth } from '../components/AuthContext';
import './Home.scss';

const Home = ({ lightMode }) => {
  const [videoEnded, setVideoEnded] = useState(false);
  const { isLoggedIn } = useAuth();

  const [books, setBooks] = useState({
    carousel: [],
    recentlyUpdated: [],
    manhwa: [],
    manhua: [],
    manga: [],
    lightNovel: [],
  });

  // Hardcoded total/numSources to account for the initial load time
  const [numBooks, setNumBooks] = useState({
    manga: 0,
    manhua: 0,
    manhwa: 0,
    lightNovel: 0,
    total: 5071,
    numSources: 31,
  });

  useEffect(() => {
    const fetchCarouselBooks = async () => {
      try {
        const response = await fetch(`${process.env.REACT_APP_API_URL}/centralized_API_backend/api/home-novels/unlogged`);
        if (!response.ok) {
          throw new Error(`HTTP error! status: ${response.status}`);
        }
        const data = await response.json();
        setBooks(prevState => ({
          ...prevState,
          carousel: data.carousel_books,
        }));
        setNumBooks(prevState => ({
          ...prevState,
          total: data.numBooks,
          numSources: data.numSources,
        }));
      } catch (error) {
        console.error('Error fetching books:', error);
      }
    };
    const fetchAllBooks = async () => {
      try {
        const response = await fetch(`${process.env.REACT_APP_API_URL}/centralized_API_backend/api/home-novels/logged`);
        if (!response.ok) {
          throw new Error(`HTTP error! status: ${response.status}`);
        }
        const data = await response.json();
        setBooks({
          carousel: data.carousel_books,
          recentlyUpdated: data.recently_updated_books,
          manga: data.manga_books,
          manhua: data.manhua_books,
          manhwa: data.manhwa_books,
          lightNovel: data.light_novel_books,
        });
        setNumBooks({
          lightNovel: data.numLightNovel,
          manhwa: data.numManhwa,
          manhua: data.numManhua,
          manga: data.numManga,
          total: data.numLightNovel+data.numManhwa+data.numManhua+data.numManga,
          numSources: data.numSources,
        });
      } catch (error) {
        console.error('Error fetching books:', error);
      }
    };
    fetchCarouselBooks();
    fetchAllBooks();
  }, []);

  const handleVideoEnd = () => {
    setVideoEnded(true);
  };

  const renderBanner = () => {
    return (
      <div className="banner-container">
        {!videoEnded && (
          <video
            className="banner"
            onEnded={handleVideoEnd}
            autoPlay
            muted
            playsInline
          >
            <source src={BannerBoyVideo} type="video/mp4" />
            Your browser does not support the video tag.
          </video>
        )}
        <img
          className={`banner ${videoEnded ? 'visible' : 'hidden'}`}
          src={BannerBoyBook}
          // src={lightMode ? BannerBoyBook : BannerSunset}
          alt="Home banner with a character reading"
        />
      </div>
    );
  };

  return (
    <div className="home">
      {renderBanner()}
      <main>
        {books && <BookCarousel books={books.carousel} />}
        {!isLoggedIn && <PreRelease />}
        {!isLoggedIn && <Welcome />}
        {!isLoggedIn && <CookieNotice />}
        {!isLoggedIn && <Statistic label="Total Number of Books" value={numBooks.total} label2="Number of Supported Sites" value2={numBooks.numSources} />}
        {isLoggedIn && <TopTenBooks title={"Recently Updated"} books={books.recentlyUpdated} numBooks={numBooks.total} />}
        {isLoggedIn && <TopTenBooks title={"Popular Manhwa"} books={books.manhwa} numBooks={numBooks.manhwa} />}
        {isLoggedIn && <TopTenBooks title={"Popular Manhua"} books={books.manhua} numBooks={numBooks.manhua} />}
        {isLoggedIn && <TopTenBooks title={"Popular Manga"} books={books.manga} numBooks={numBooks.manga} />}
        {isLoggedIn && <TopTenBooks title={"Popular Light Novels"} books={books.lightNovel} numBooks={numBooks.lightNovel} />}
        {/* TODO: Update this to be most popular (after getting users)*/}
        {/* {isLoggedIn && <TopTenBooks title={"Most Popular Series"} books={books.carousel} numBooks={numBooks.total} />} */}
      </main>
    </div>
  );
};

export default Home;
