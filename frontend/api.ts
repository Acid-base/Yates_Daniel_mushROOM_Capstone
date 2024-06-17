import axios from 'axios';

const api = axios.create({
  baseURL: 'http://localhost:5000/api', // Adjust the base URL as needed
  headers: {
    'Content-Type': 'application/json',
  },
});

// Blog API
export const fetchBlogPosts = async () => {
  const response = await api.get('/blog');
  return response.data;
};

// Mushroom API
export const fetchMushrooms = async (searchTerm = '', page = 1) => {
  const response = await api.get('/mushrooms', {
    params: { q: searchTerm, page },
  });
  return response.data;
};

export const addMushroom = async (mushroomData) => {
  const response = await api.post('/mushrooms', mushroomData);
  return response.data;
};

// User API
export const registerUser = async (userData) => {
  const response = await api.post('/users/register', userData);
  return response.data;
};

export const loginUser = async (credentials) => {
  const response = await api.post('/users/login', credentials);
  return response.data;
};

export const fetchUserProfile = async () => {
  const response = await api.get('/users/me');
  return response.data;
};

export const updateUserProfile = async (userId, userData) => {
  const response = await api.put(`/users/${userId}/update`, userData);
  return response.data;
};

export const toggleFavorite = async (mushroomId) => {
  const response = await api.post(`/users/favorites/${mushroomId}`);
  return response.data;
};

export default api;
