import React, { useState, useEffect } from 'react';
import { Navigate } from 'react-router-dom';
import { useAuth } from '../contexts/AuthContext';
import { moviesAPI, userAPI } from '../services/api';
import MovieCard from '../components/MovieCard';
import SearchBar from '../components/SearchBar';

const Dashboard = () => {
  const { user, isAuthenticated } = useAuth();
  const [recommendations, setRecommendations] = useState([]);
  const [watchlist, setWatchlist] = useState([]);
  const [searchResults, setSearchResults] = useState([]);
  const [loading, setLoading] = useState(true);
  const [searchQuery, setSearchQuery] = useState('');
  const [activeTab, setActiveTab] = useState('recommendations');
  const [error, setError] = useState('');

  useEffect(() => {
    if (isAuthenticated) {
      fetchDashboardData();
    }
  }, [isAuthenticated]);

  const fetchDashboardData = async () => {
    try {
      setLoading(true);
      const [recResponse, watchlistResponse] = await Promise.all([
        moviesAPI.getUserRecommendations().catch(() => ({ data: [] })),
        userAPI.getWatchlist().catch(() => ({ data: [] }))
      ]);
      
      setRecommendations(recResponse.data.results || recResponse.data || []);
      setWatchlist(watchlistResponse.data.results || watchlistResponse.data || []);
    } catch (error) {
      setError('Failed to load dashboard data');
      console.error('Dashboard error:', error);
    } finally {
      setLoading(false);
    }
  };

  const handleSearch = async (query) => {
    if (!query) {
      setSearchResults([]);
      setSearchQuery('');
      return;
    }

    try {
      setSearchQuery(query);
      const response = await moviesAPI.searchMovies(query);
      setSearchResults(response.data.results || response.data || []);
      setActiveTab('search');
    } catch (error) {
      setError('Search failed');
      console.error('Search error:', error);
    }
  };

  const handleTabChange = (tab) => {
    setActiveTab(tab);
    if (tab !== 'search') {
      setSearchQuery('');
      setSearchResults([]);
    }
  };

  if (!isAuthenticated) {
    return <Navigate to="/login" replace />;
  }

  const getCurrentMovies = () => {
    switch (activeTab) {
      case 'recommendations':
        // Recommendations come in a nested structure with 'recommendations' field
        return recommendations.recommendations || recommendations;
      case 'watchlist':
        // Watchlist items have nested movie objects, extract them
        return watchlist.map(item => item.movie || item);
      case 'search':
        return searchResults;
      default:
        return [];
    }
  };

  const getCurrentTitle = () => {
    switch (activeTab) {
      case 'recommendations':
        return 'Recommended for You';
      case 'watchlist':
        return 'Your Watchlist';
      case 'search':
        return `Search Results for "${searchQuery}"`;
      default:
        return '';
    }
  };

  return (
    <div className="container" style={{ paddingTop: '20px' }}>
      {/* Welcome Section */}
      <div style={{ marginBottom: '30px' }}>
        <h1>Welcome back, {user?.first_name || user?.username}! 👋</h1>
        <p style={{ color: '#666', fontSize: '1.1rem' }}>
          Discover new movies and manage your watchlist
        </p>
      </div>

      {/* Search Bar */}
      <SearchBar onSearch={handleSearch} />

      {error && (
        <div className="error" style={{ textAlign: 'center', marginBottom: '20px' }}>
          {error}
        </div>
      )}

      {/* Tabs */}
      <div style={{ marginBottom: '30px' }}>
        <div style={{ 
          display: 'flex', 
          gap: '10px', 
          borderBottom: '2px solid #f0f0f0',
          marginBottom: '20px'
        }}>
          <button
            onClick={() => handleTabChange('recommendations')}
            style={{
              padding: '10px 20px',
              border: 'none',
              background: 'none',
              cursor: 'pointer',
              borderBottom: activeTab === 'recommendations' ? '2px solid #007bff' : 'none',
              color: activeTab === 'recommendations' ? '#007bff' : '#666',
              fontWeight: activeTab === 'recommendations' ? 'bold' : 'normal'
            }}
          >
            Recommendations ({recommendations.length})
          </button>
          
          <button
            onClick={() => handleTabChange('watchlist')}
            style={{
              padding: '10px 20px',
              border: 'none',
              background: 'none',
              cursor: 'pointer',
              borderBottom: activeTab === 'watchlist' ? '2px solid #007bff' : 'none',
              color: activeTab === 'watchlist' ? '#007bff' : '#666',
              fontWeight: activeTab === 'watchlist' ? 'bold' : 'normal'
            }}
          >
            Watchlist ({watchlist.length})
          </button>
          
          {searchQuery && (
            <button
              onClick={() => handleTabChange('search')}
              style={{
                padding: '10px 20px',
                border: 'none',
                background: 'none',
                cursor: 'pointer',
                borderBottom: activeTab === 'search' ? '2px solid #007bff' : 'none',
                color: activeTab === 'search' ? '#007bff' : '#666',
                fontWeight: activeTab === 'search' ? 'bold' : 'normal'
              }}
            >
              Search Results ({searchResults.length})
            </button>
          )}
        </div>

        <h2>{getCurrentTitle()}</h2>
      </div>

      {/* Content */}
      {loading ? (
        <div className="loading">Loading...</div>
      ) : (
        <div>
          {getCurrentMovies().length > 0 ? (
            <div className="movie-grid">
              {getCurrentMovies().map((movie) => (
                <MovieCard key={movie.id} movie={movie} />
              ))}
            </div>
          ) : (
            <div style={{ textAlign: 'center', padding: '50px', color: '#666' }}>
              {activeTab === 'recommendations' && 'No recommendations available yet. Rate some movies to get personalized suggestions!'}
              {activeTab === 'watchlist' && 'Your watchlist is empty. Add some movies to watch later!'}
              {activeTab === 'search' && `No results found for "${searchQuery}"`}
            </div>
          )}
        </div>
      )}
    </div>
  );
};

export default Dashboard;