import React from 'react';
import Welcome from '../components/Welcome.js';
import BookCarousel from '../components/BookCarousel.js';
import TopTenBooks from '../components/TopTenBooks.js';
import Statistic from '../components/Statistic.js';
import "slick-carousel/slick/slick.css"; 
import "slick-carousel/slick/slick-theme.css";
// import BannerDark from '../assets/BannerDark.png';
import BannerBoyBook from '../assets/BannerBoyBook.png';
import BannerSunset from '../assets/BannerSunset.png';
import { useAuth } from '../components/AuthContext';
import './Home.scss';

const Home = ({ books, lightMode }) => {
  const { isLoggedIn } = useAuth();

  // Ensure books is an array before calling .filter and .sort
  const isBooksArray = Array.isArray(books);

  const mangaBooks = isBooksArray ? books.filter(book => book.novel_type === "Manga") : [];
  const manhuaBooks = isBooksArray ? books.filter(book => book.novel_type === "Manhua") : [];
  const manhwaBooks = isBooksArray ? books.filter(book => book.novel_type === "Manhwa") : [];
  const lightNovelBooks = isBooksArray ? books.filter(book => book.novel_type === "Light Novel") : [];
  const recentlyUpdatedBooks = isBooksArray ? books.sort((a, b) => new Date(b.updated_on) - new Date(a.updated_on)) : [];

  // Make a copy of the books array and sort it by rating
  const sortedBooksByRating = isBooksArray ? [...books].sort((a, b) => parseFloat(b.rating) - parseFloat(a.rating)) : [];

  return (
    <div className="home">
      {!isLoggedIn 
        ? lightMode 
          ? <img className="banner" src={BannerBoyBook} alt="Home banner with a character reading"/>
          // ? <img className="banner" src={BannerDark} alt="Home banner with a character reading"/>
          : <img className="banner" src={BannerSunset} alt="Home banner with a character reading"/>
        : null
      }
      <main>
        {isBooksArray && <BookCarousel books={sortedBooksByRating.slice(0, 20)} />}
        {!isLoggedIn && <Welcome />}
        {!isLoggedIn && <Statistic label="Total Number of Books" value={isBooksArray ? books.length : 0} />}
        {isLoggedIn && <TopTenBooks title={"Recently Updated"} books={recentlyUpdatedBooks} />}
        {isLoggedIn && <TopTenBooks title={"Most Popular Manhwa This Month"} books={manhwaBooks} />}
        {isLoggedIn && <TopTenBooks title={"Most Popular Manhua This Month"} books={manhuaBooks} />}
        {isLoggedIn && <TopTenBooks title={"Most Popular Manga This Month"} books={mangaBooks} />}
        {isLoggedIn && <TopTenBooks title={"Most Popular Light Novels This Month"} books={lightNovelBooks} />}
        {isLoggedIn && <TopTenBooks title={"Most Popular Series"} books={sortedBooksByRating} />}
      </main>
    </div>
  );
};

export default Home;
