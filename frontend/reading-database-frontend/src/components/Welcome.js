import React from 'react';
import './Welcome.scss';

const Welcome = () => {
  return (
    <div className="welcome">
      <h1>Hi there 👋 &nbsp;&nbsp; Welcome to Haneul!</h1>
      <p>
        This platform was born out of a personal necessity and a commitment to ethical technology.
        As a consumer, I understand the challenges manga and light novel enthusiasts face
        from keeping track of the latest chapters across various platforms.
        Traditional methods like bookmarking on publisher sites means you've got at least 5 pinned websites, 
        and relying on aggregator sites is equally disappointing due to the aggregator 
        profiting while the original publisher drops the book due to lack of support.
        <br /><br />
        To address these challenges, I've built a centralized Manga and Light Novel Tracking 
        platform where you can easily access, manage, and track your manga and light novel collections.
        My goal is to offer a reliable and ethical service for fellow enthusiasts while supporting 
        original publishers.
      </p>
    </div>
  );
}

export default Welcome;
