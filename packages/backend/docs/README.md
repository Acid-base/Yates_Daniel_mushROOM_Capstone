Mushroom Explorer Backend
This repository contains the backend code for the Mushroom Explorer application. It's built using Node.js, Express.js, MongoDB, and Mongoose.

Project Structure
backend/
├── server.js
├── mongo
│   ├── models
│   │   ├── Observation.js
│   │   ├── Image.js
│   │   └── Name.js
│   └── db.js
└── scripts
    └── populateMushrooms.js

Installation
Install Node.js and npm (or your preferred package manager).
Navigate to the project directory: cd backend
Install the dependencies: npm install
Create a .env file in the root directory and add the following environment variables:
MONGODB_URI: Your MongoDB connection string
MUSHROOM_OBSERVER_API_KEY: Your Mushroom Observer API key
Running the Server
Start the server: npm start
API Endpoints
Observations
/api/observations (GET): Retrieves a list of observations with pagination.
Query Parameters:
page (optional): The page number to retrieve. Default: 1.
limit (optional): The number of observations per page. Default: 20.
Response: { observations: [ { id, type, date, ... }, ... ], currentPage: 1, totalPages: 10 }
/api/observations/:id (GET): Retrieves details of a specific observation by ID.
Response: { id, type, date, ... }
/api/observations/:id/images (GET): Retrieves images associated with a specific observation by ID.
Response: [ { id, url, observationId, ... }, ... ]
/api/search/observations (GET): Searches observations by name.
Query Parameter: q: The search term.
Response: [ { id, type, date, ... }, ... ]
Names
/api/names (GET): Retrieves a list of mushroom names with pagination.
Query Parameters:
page (optional): The page number to retrieve. Default: 1.
limit (optional): The number of names per page. Default: 20.
Response: { names: [ { id, name, author, rank, ... }, ... ], currentPage: 1, totalPages: 10 }
Data Fetching
The backend continuously fetches data from the Mushroom Observer API and stores it in the MongoDB database. This ensures that the application has up-to-date information.
Future Enhancements
Implement a more robust search functionality with filtering and sorting options.
Add support for user authentication and authorization.
Create endpoints for managing user profiles and favorites.
Integrate a third-party geolocation service to provide more accurate region information.
Documentation
For detailed API documentation, see the docs/API Reference.md file.



