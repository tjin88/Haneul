import React from 'react';
import './Welcome.scss';

const Welcome = () => {
  return (
    <div className="welcome">
      <h1>Hi there 👋 &nbsp; Welcome to Haneul!</h1>
      <p>
        This platform was born out of a personal necessity and a commitment to supporting authors and translators.
        As someone who enjoys reading manga and light novels, I've always struggled to keep track of the latest chapters.
        While I'm not proud of it, that does come in the form of either having 10+ tabs open or relying on aggregator sites.
        <br /><br />
        Since the latter is slowly killing the translators and authors,
        I've decided to take matters into my own hands.
        <br /><br />
        Haneul is a platform that aims to provide a centralized database for manga and light novels.
        That's it! Just a simple, easy-to-use platform to keep track of your favorite series.
        <br /><br />
        Please join me in re-introducing the world to the joy of reading and supporting the creators.
      </p>
    </div>
  );
}

export default Welcome;
