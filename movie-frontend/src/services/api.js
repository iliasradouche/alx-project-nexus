// src/api.js (or wherever this lives)
import axios from 'axios';

const PROD = process.env.NODE_ENV === 'production';

// Prefer Netlify proxy in production (no CORS). If you *really* want to hit
// the backend directly, set REACT_APP_API_URL to the full https URL.
const base =
  (process.env.REACT_APP_API_URL && process.env.REACT_APP_API_URL.trim()) ||
  (PROD ? '/api' : 'http://127.0.0.1:8000/api');

const ensureTrailingSlash = (s) => (s.endsWith('/') ? s : s + '/');

const api = axios.create({
  baseURL: ensureTrailingSlash(base),
  headers: { 'Content-Type': 'application/json' },
  withCredentials: false, // you're using Bearer tokens, not cookies
});

// Attach Bearer token if present
api.interceptors.request.use(
  (config) => {
    const token = localStorage.getItem('token');
    if (token) config.headers.Authorization = `Bearer ${token}`;
    return config;
  },
  (error) => Promise.reject(error)
);

// Auth API
export const authAPI = {
  login: (credentials) => api.post('auth/login/', credentials),
  register: (userData) => api.post('auth/register/', userData),
  logout: () => api.post('auth/logout/'),
  getProfile: () => api.get('auth/profile/'),
};

// Movies API
export const moviesAPI = {
  getMovies: (params = {}) => api.get('movies/', { params }),
  getMovie: (id) => api.get(`movies/${id}/`),
  searchMovies: (query) => api.post('movies/search/', { query, page: 1 }),
  getGenres: () => api.get('movies/genres/'),
  getRecommendations: (movieId) => api.get(`movies/${movieId}/recommendations/`),
  getUserRecommendations: () => api.get('movies/user/recommendations/'),
};

// User interactions API
export const userAPI = {
  addToWatchlist: (movieId) => api.post('movies/watchlist/', { movie_id: movieId }),
  removeFromWatchlist: (movieId) => api.delete(`movies/watchlist/${movieId}/`),
  getWatchlist: () => api.get('movies/watchlist/'),
  rateMovie: (movieId, rating) => api.post('movies/ratings/', { movie_id: movieId, rating }),
  getUserRatings: () => api.get('movies/ratings/'),
};

export default api;
