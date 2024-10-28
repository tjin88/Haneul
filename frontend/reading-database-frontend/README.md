# This Project was created using REACT, hosted on Firebase

### Start locally
- npm start

### Deploy
- npm run build
- firebase deploy

### Adjust between deployed and localhost server
Go to package.json and adjust the "proxy":
    - To use the deployed server: "proxy": "https://haneul.onrender.com/",
    - To use the local server: "proxy": "http://127.0.0.1:8000/",
