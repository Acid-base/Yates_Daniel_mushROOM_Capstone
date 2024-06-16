## Installation

1. Install Node.js and npm (or your preferred package manager).
2. Navigate to the project directory: `cd backend`
3. Install the dependencies: `npm install`
4. Create a `.env` file in the root directory and add the following environment variables:
   - `MONGODB_URI`: Your MongoDB connection string
   - `SECRET_KEY`: A strong secret key for JWT authentication (replace `your_secret_key` in `userController.js`)

## Running the Server

Start the server: `npm start`

## API Endpoints

### Users

- `/users/register` (POST): Registers a new user.
  - **Request Body:** `{ name, email, password }`
  - **Response:**
    - `201 (Created)`: `{ message: 'User registered successfully!', user: { id, name, email }, token }`
    - `409 (Conflict)`: `{ error: 'Email already exists' }`
    - `500 (Internal Server Error)`: `{ error: 'Failed to register user' }`
- `/users/login` (POST): Logs in a user.
  - **Request Body:** `{ email, password }`
  - **Response:**
    - `200 (OK)`: `{ message: 'Login successful!', user: { id, name, email }, token }`
    - `401 (Unauthorized)`: `{ error: 'Invalid credentials' }`
    - `500 (Internal Server Error)`: `{ error: 'Failed to log in user' }`
- `/users/:userId/update` (PUT): Updates a user's profile. Requires authentication.
  - **Request Body:** `{ name, email, password, location, avatarUrl, bio }`
  - **Response:**
    - `200 (OK)`: `{ message: 'Profile updated successfully!', user: { id, name, email, ... } }`
    - `404 (Not Found)`: `{ error: 'User not found' }`
    - `409 (Conflict)`: `{ error: 'Email already exists' }`
    - `500 (Internal Server Error)`: `{ error: 'Failed to update profile' }`
- `/users/favorites` (GET): Retrieves a list of the authenticated user's favorite mushrooms. Requires authentication.
  - **Response:** `[ { scientificName, latitude, longitude, imageUrl, ... }, ... ]`
- `/users/me` (GET): Retrieves the authenticated user's information. Requires authentication.
  - **Response:** `{ name, email, location, avatarUrl, bio, favorites: [ { scientificName, latitude, longitude, imageUrl, ... }, ... ], savedMushrooms: [ { scientificName, latitude, longitude, imageUrl, ... }, ... ] }`

### Mushrooms

- `/mushrooms` (GET): Retrieves a list of mushrooms. Requires authentication.
  - **Query Parameter:** `q` (optional): Search term
  - **Response:** `[ { scientificName, latitude, longitude, imageUrl, ... }, ... ]`
- `/mushrooms/:mushroomId/favorites` (POST): Toggles a mushroom as a favorite for the authenticated user. Requires authentication.
  - **Response:**
    - `200 (OK)`: `{ message: 'Added to favorites' }` or `{ message: 'Removed from favorites' }`
    - `404 (Not Found)`: `{ error: 'Mushroom not found' }`
    - `500 (Internal Server Error)`: `{ error: 'Failed to toggle favorite' }`

## Authentication

The backend uses JWT authentication. When a user registers or logs in, a JWT token is generated and returned in the response. This token should be included in subsequent requests to authenticated endpoints.

## Future Enhancements

- Implement a more robust search functionality with filtering and sorting options.
- Add pagination to the `/mushrooms` endpoint to handle large datasets.
