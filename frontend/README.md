
## Installation

1. Install Node.js and npm (or your preferred package manager).
2. Navigate to the project directory: `cd frontend`
3. Install the dependencies: `npm install`

## Running the Development Server

1. Start the development server: `npm run dev` 

## Features

* **Search:**  Search for mushrooms by common name or scientific name.
* **Details:** View detailed information about individual mushrooms, including images, descriptions, and location.
* **Favorites:** Save your favorite mushrooms for easy access.
* **User Profile:** Manage your profile, view saved favorites, and update your information.
* **Blog:** Read mushroom-related news and articles.
* **About:** Learn more about the Mushroom Explorer project.

## Technologies Used

* **React:** A JavaScript library for building user interfaces.
* **Vite:** A fast development server and build tool for web applications.
* **React Router:** A routing library for single-page applications.
* **Axios:** A Promise-based HTTP client for making API requests.

## Testing

The frontend uses Jest for unit and integration tests and Cypress for end-to-end (E2E) tests.  You can run tests with:

* **Unit & Integration Tests:** `npm run test`
* **E2E Tests:** `npm run test:e2e`

## Contributing

Contributions are welcome! Please see the `CONTRIBUTING.md` file for guidelines.

## Future Enhancements

* Implement a more robust search functionality with filtering and sorting options.
* Add pagination to the search results.
* Enhance the user profile with more features, such as saving mushrooms to a list.
* Add social media sharing for mushroom details.
* Create a more visually appealing user interface.

## Getting Started

The frontend makes API calls to the backend server. You will need to run the backend server first before starting the frontend development server.  

### Backend Setup

1.  Clone the monorepo: git clone https://github.com/Acid-base/Yates_Daniel_mushROOM_Capstone
2.  Navigate to the backend directory: `cd backend`
3.  Install backend dependencies: `npm install`
4.  Create a `.env` file and set the `MONGODB_URI` and `SECRET_KEY` environment variables.
5.  Start the backend server: `npm start` 

### Frontend Setup

2.  Navigate to the frontend directory: `cd ../frontend`
3.  Install frontend dependencies: `npm install`
4.  Start the frontend development server: `npm run dev`

This will open the application in your browser, and you can begin using Mushroom Explorer!


