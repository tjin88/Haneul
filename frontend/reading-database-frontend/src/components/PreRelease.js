import React from 'react';
import './PreRelease.scss';

const PreRelease = () => {
  return (
    <div className="pre-release">
      <h1>🎉🎉 In honour of Wordle #1,087 (June 10, 2024), Haneul is officially doing it's pre-release! 🎉🎉</h1>
      <p>
        Please note, since this is in pre-release, there may be bugs and missing features.
        One known issue is mobile responsiveness, which is currently being worked on.
        For now, only desktop is supported.
        There will also be up to 50 seconds of delay for the server to turn on, should it be inactive for over 15 minutes.
        You'll know that the server is up and running when you see the book images appear above this message.
        <br /> 
        If you have any questions, comments, feature ideas, or find any bugs, please reach out to me at tjin368@gmail.com!
        <br />
        I hope you enjoy the site! 😊
      </p>
    </div>
  );
}

export default PreRelease;
