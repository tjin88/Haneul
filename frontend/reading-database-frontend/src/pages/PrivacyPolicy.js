import React from 'react';
import './PrivacyPolicy.scss';

const PrivacyPolicy = () => {
  return (
    <div className="privacy-policy">
      <h1>Privacy Policy</h1>
      <p>Last updated: June 3, 2024</p>

      <h2>Introduction</h2>
      <p>
        Welcome to Haneul. We value your privacy and are committed to protecting your personal data. This privacy policy explains how we collect, use, and protect your information when you use our services, including the website and browser extensions.
      </p>

      <h2>Information We Collect</h2>
      <p>
        We collect the following personal data to provide and improve our services:
      </p>
      <ul>
        <li><strong>Username (email):</strong> Used for account creation, login, and communication.</li>
        <li><strong>Password:</strong> Stored securely and used for authentication purposes.</li>
      </ul>

      <h2>How We Use Your Information</h2>
      <p>
        We use the collected information for the following purposes:
      </p>
      <ul>
        <li>To provide and maintain our services, including storing and managing your book entries across various websites.</li>
        <li>To authenticate users and manage access to the website and its features.</li>
        <li>To enhance user experience with our browser extension, which updates your most recently read chapter if you are on a supported site.</li>
        <li>To create a centralized database of book entries from various publishers, redirecting user traffic to the original translators.</li>
      </ul>

      <h2>Data Scraping</h2>
      <p>
        Our website scrapes data from various publishers to provide a centralized database for your convenience. The purpose of this data scraping is not for malignant purposes, but rather to redirect user traffic to the original translators and provide a seamless reading experience. We respect the work of original translators and ensure that our users are directed to the original sources.
      </p>

      <h2>Browser Extension</h2>
      <p>
        Our browser extension for Chrome, Edge, and Firefox helps you track your reading progress more conveniently. It monitors the websites you visit, and if you are on a supported site, it automatically updates your database with the most recently read chapter. The extension is an optional quality of life feature and is not necessary for using our core services.
      </p>

      <h2>Data Security</h2>
      <p>
        We implement appropriate technical and organizational measures to protect your personal data from unauthorized access, use, or disclosure. Your password is stored securely, and we use encryption to protect sensitive information.
      </p>

      <h2>Your Rights</h2>
      <p>
        You have the right to access, correct, or delete your personal data at any time. If you have any concerns about your data, please contact us at tjin368@gmail.com.
      </p>

      <h2>Changes to This Privacy Policy</h2>
      <p>
        We may update this privacy policy from time to time. We will notify you of any changes by posting the new privacy policy on this page and updating the "Last updated" date at the top of this policy.
      </p>

      <h2>Contact Us</h2>
      <p>
        If you have any questions about this privacy policy, please contact us at:
      </p>
      <p>Email: tjin368@gmail.com</p>
    </div>
  );
};

export default PrivacyPolicy;