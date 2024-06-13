// backend/helpers.js
import axios from 'axios';
import rateLimit from 'axios-rate-limit';

// Rate limiting (adjust as needed)
const api = rateLimit(axios.create(), { maxRequests: 1, perMilliseconds: 6000 });

// Helper function to get the region from coordinates
async function getRegionFromCoordinates(latitude, longitude) {
  // ... (Logic to get region from coordinates using a geolocation API)
  return 'Unknown'; // Or the fetched region
}

// Other helper functions (e.g., for data transformation)

export default {
  getRegionFromCoordinates,
  // ... other helper functions
};
