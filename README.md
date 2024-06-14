Project Root
├── frontend
│   ├── src
│   │   ├── components
│   │   │   ├── BlogPost.jsx
│   │   │   ├── MushroomCard.jsx
│   │   │   ├── SearchBar.jsx
│   │   │   └── UserCard.jsx
│   │   ├── App.jsx
│   │   ├── pages
│   │   │   ├── Blog.jsx
│   │   │   ├── Home.jsx
│   │   │   ├── Mushrooms.jsx
│   │   │   ├── Profile.jsx
│   │   │   └── User.jsx
│   │   ├── api
│   │   │   ├── blog.js
│   │   │   ├── mushrooms.js
│   │   │   └── users.js
│   │   ├── utils
│   │   │   └── dateFormatter.js
│   │   ├── App.css
│   │   └── index.html
│   ├── vite.config.js
│   └── README.md
├── backend
│   ├── server.js
│   ├── middleware
│   │   ├── auth.js
│   │   ├── errorHandler.js
│   │   ├── mushroomService.js
│   │   ├── validate.js
│   │   └── user.js
│   ├── routes
│   │   ├── UserRoutes.js
│   │   ├── BlogRoutes.js
│   │   └── MushroomRoutes.js
│   ├── models
│   │   ├── BlogPostModel.js
│   │   ├── User.js
│   │   └── MushroomModel.js
│   ├── helpers
│   │   └── utils.js
│   ├── .eslintrc.js
│   └── eslint.config.mjs
├── package.json
└── README.md

Getting Started
This monorepo contains both the frontend and backend components of the Mushroom Explorer application. Here's how to set up and run the application:

Backend Setup
Clone the monorepo: git clone https://github.com/Acid-base/Yates_Daniel_mushROOM_Capstone
Navigate to the backend directory: cd backend
Install dependencies: npm install
Create a .env file: Create a file named .env in the backend directory and set the following environment variables:
MONGODB_URI: Your MongoDB connection string.
SECRET_KEY: A secret key for JWT authentication.
Start the backend server: npm start

Frontend Setup
Navigate to the frontend directory: cd ../frontend
Install dependencies: npm install
Start the frontend development server: npm run dev
This will open the application in your browser, and you can begin using Mushroom Explorer!

Features
- Search: Search for mushrooms by common name or scientific name.
- Details: View detailed information about individual mushrooms, including images, descriptions, and location.
- Favorites: Save your favorite mushrooms for easy access.
- User Profile: Manage your profile, view saved favorites, and update your information.
- Blog: Read mushroom-related news and articles.
- About: Learn more about the Mushroom Explorer project.

Technologies Used
Frontend:
- React: A JavaScript library for building user interfaces.
- Vite: A fast development server and build tool for web applications.
- React Router: A routing library for single-page applications.
- Axios: A Promise-based HTTP client for making API requests.

Backend:
- Node.js: JavaScript runtime environment.
- Express: A web framework for Node.js.
- Mongoose: A MongoDB object modeling tool for Node.js.
- MongoDB: A NoSQL database.
- JSON Web Tokens (JWT): A standard for securely transmitting information between parties as JSON objects.
- ESLint: A static code analysis tool for identifying and fixing problems in JavaScript code.

Future Enhancements
- Implement a more robust search functionality with filtering and sorting options.
- Add pagination to the search results.
- Enhance the user profile with more features, such as saving mushrooms to a list.
- Add social media sharing for mushroom details.
- Create a more visually appealing user interface.

For more detailed information, refer to the README files in the frontend and backend directories.
