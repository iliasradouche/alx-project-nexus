import axios from 'axios';

// Create axios instance with base configuration
const api = axios.create({
  baseURL: process.env.REACT_APP_API_URL || 'http://127.0.0.1:8000/api',
  headers: {
    'Content-Type': 'application/json',
  },
});

// Request interceptor to add auth token
api.interceptors.request.use(
  (config) => {
    const token = localStorage.getItem('token');
    if (token) {
      config.headers.Authorization = `Bearer ${token}`;
    }
    return config;
  },
  (error) => {
    return Promise.reject(error);
  }
);

// Response interceptor to handle errors
api.interceptors.response.use(
  (response) => response,
  (error) => {
    if (error.response?.status === 401) {
      localStorage.removeItem('token');
      localStorage.removeItem('user');
      window.location.href = '/login';
    }
    return Promise.reject(error);
  }
);

// Auth API
export const authAPI = {
  login: (credentials) => api.post('/auth/login/', credentials),
  register: (userData) => api.post('/auth/register/', userData),
  logout: () => api.post('/auth/logout/'),
  getProfile: () => api.get('/auth/profile/'),
};

// Movies API
export const moviesAPI = {
  getMovies: (params = {}) => api.get('/movies/', { params }),
  getMovie: (id) => api.get(`/movies/${id}/`),
  searchMovies: (query) => api.post('/movies/search/', { query: query, page: 1 }),
  getGenres: () => api.get('/movies/genres/'),
  getRecommendations: (movieId) => api.get(`/movies/${movieId}/recommendations/`),
  getUserRecommendations: () => api.get('/movies/user/recommendations/'),
};

// User interactions API
export const userAPI = {
  addToWatchlist: (movieId) => api.post('/movies/watchlist/', { movie_id: movieId }),
  removeFromWatchlist: (movieId) => api.delete(`/movies/watchlist/${movieId}/`),
  getWatchlist: () => api.get('/movies/watchlist/'),
  rateMovie: (movieId, rating) => api.post('/movies/ratings/', { movie_id: movieId, rating }),
  getUserRatings: () => api.get('/movies/ratings/'),
};

export default api;