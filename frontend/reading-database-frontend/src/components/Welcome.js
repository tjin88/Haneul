import React from 'react';
import './Welcome.scss';

const Welcome = () => {
  return (
    <div className="welcome">
      <h1>Welcome to the Manga and Light Novel Tracking Platform</h1>
      <p>
        This project was born out of a personal necessity and a commitment to ethical technology.
        I understand the challenges manga and light novel enthusiasts face - from keeping track of 
        the latest chapters to managing personal collections. Traditional methods like bookmarking 
        and relying on aggregator sites often lead to frustrations and ethical dilemmas, as many 
        aggregator sites profit from content without supporting the original publishers.
      </p>
      <p>
        To address these challenges, I've built a centralized platform where you can easily access,
        manage, and track your manga and light novel collections. As my first full-stack project, 
        this platform represents a blend of technical skills and a passion for reading. 
        My goal is to offer a reliable and ethical service for fellow enthusiasts. 
        I hope this platform becomes a valuable tool for your reading journey.
      </p>
      <p>
        Dive into the world of Manga and Light Novels today and join us in revolutionizing 
        how we access and enjoy our favorite reads!
      </p>
    </div>
  );
}

export default Welcome;
