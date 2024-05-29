import React from 'react';
import Slider from 'react-slick';
import BookCard from './BookCard';
import './BookCarousel.scss';
import 'slick-carousel/slick/slick.css'; 
import 'slick-carousel/slick/slick-theme.css';

const BookCarousel = ({ books }) => {
  const settings = {
    dots: true, // Enables dot indicators below the carousel
    infinite: true,
    speed: 500,
    slidesToShow: 6, // Shows 6 books at once
    slidesToScroll: 1,
    draggable: true,
    swipe: true,
    swipeToSlide: true, // Allows scrolling with a trackpad --> TODO: Still working on this!
    lazyLoad: false,
    autoplay: true,
    autoplaySpeed: 2000,
    pauseOnDotsHover: true,
    pauseOnHover: false,
    responsive: [
      {
        breakpoint: 1024,
        settings: {
          slidesToShow: 3,
        },
      },
      {
        breakpoint: 600,
        settings: {
          slidesToShow: 2,
        },
      },
      {
        breakpoint: 480,
        settings: {
          slidesToShow: 1,
        },
      },
    ],
  };

  return (
    <div className='carousel-container'>
        <div className='book-carousel'>
            <Slider {...settings}>
                {books && books.map((book, index) => (
                    <BookCard key={index} {...book} />
                ))}
            </Slider>
        </div>
    </div>
  );
};

export default BookCarousel;
