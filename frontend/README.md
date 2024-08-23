# Mushroom Explorer Frontend

This is the frontend for the Mushroom Explorer application, built with React, TypeScript, and Vite.

## Installation

1. Navigate to the frontend directory: `cd frontend`
2. Install the dependencies: `npm install`

## Running the Frontend

Start the development server: `npm run dev`

## Routes

The frontend application includes the following routes:

- `/`: Home page
- `/profile`: User profile page
- `/blog`: Blog page
- `/about`: About page
- `/mushroom/:mushroomId`: Mushroom details page

## TypeScript Interfaces

The following TypeScript interfaces are used in the project and are defined in `frontend/src/types/index.ts`:

### User Interface

```typescript
export interface User {
  id: string;
  name: string;
  email: string;
  location?: string;
  avatarUrl?: string;
  bio?: string;
  favorites: Mushroom[];
  savedMushrooms: Mushroom[];
}

export interface Mushroom {
  scientificName: string;
  latitude: number;
  longitude: number;
  imageUrl: string;
  description?: string;
  commonName?: string;
  family?: string;
  genus?: string;
  region?: string;
  gallery?: { url: string; thumbnailUrl: string }[];
  kingdom?: string;
  phylum?: string;
  class?: string;
  order?: string;
  habitat?: string;
  edibility?: string;
  distribution?: string;
  wikipediaUrl?: string;
  mushroomObserverUrl?: string;
}
export interface APIError {
  error: string;
}

Features
Search: Search for mushrooms by common name or scientific name.
Details: View detailed information about individual mushrooms, including images, descriptions, and location.
Favorites: Save your favorite mushrooms for easy access.
User Profile: Manage your profile, view saved favorites, and update your information.
Blog: Read mushroom-related news and articles.
About: Learn more about the Mushroom Explorer project.
Technologies Used
Frontend
React: A JavaScript library for building user interfaces.
Vite: A fast development server and build tool for web applications.
React Router: A routing library for single-page applications.
Axios: A Promise-based HTTP client for making API requests.
TanStack Query: For data fetching and state management.
Future Enhancements
Implement a more robust search functionality with filtering and sorting options.
Add pagination to the mushroom list to handle large datasets.
Contributing
Contributions are welcome! Please open an issue or submit a pull request.

License
This project is licensed under the MIT License.

### Summary of Changes

1. **Installation and Running Instructions**: Added instructions for installing dependencies and running the development server.
2. **Routes**: Listed the routes available in the frontend application.
3. **TypeScript Interfaces**: Included the `User`, `Mushroom`, and `APIError` interfaces from `frontend/src/types/index.ts`.
4. **Features**: Listed the features of the application.
5. **Technologies Used**: Listed the technologies used in the frontend.
6. **Future Enhancements**: Added a section for future enhancements.
7. **Contributing and License**: Added sections for contributing and license information.

By including these details, the `README.md` file provides a comprehensive overview of the frontend application, its routes, and the TypeScript interfaces used.
```
