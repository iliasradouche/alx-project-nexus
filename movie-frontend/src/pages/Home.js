import React, { useState, useEffect } from 'react';
import { Link } from 'react-router-dom';
import { moviesAPI } from '../services/api';
import { useAuth } from '../contexts/AuthContext';
import MovieCard from '../components/MovieCard';
import SearchBar from '../components/SearchBar';
import MovieSlider from '../components/MovieSlider';

const Home = () => {
  const [movies, setMovies] = useState([]);
  const [searchResults, setSearchResults] = useState([]);
  const [loading, setLoading] = useState(true);
  const [searching, setSearching] = useState(false);
  const [error, setError] = useState('');
  const [searchQuery, setSearchQuery] = useState('');
  const [currentPage, setCurrentPage] = useState(1);
  const [totalPages, setTotalPages] = useState(1);
  const [hasNext, setHasNext] = useState(false);
  const [hasPrevious, setHasPrevious] = useState(false);
  const { isAuthenticated } = useAuth();

  useEffect(() => {
    fetchMovies();
  }, []);

  const fetchMovies = async (page = 1) => {
    try {
      setLoading(true);
      const response = await moviesAPI.getMovies({ page_size: 12, page });
      const data = response.data;
      
      setMovies(data.results || data);
      setCurrentPage(page);
      
      // Handle pagination metadata
      if (data.page_info) {
        setTotalPages(data.page_info.total_pages);
        setHasNext(data.page_info.has_next);
        setHasPrevious(data.page_info.has_previous);
      } else {
        // Fallback for standard DRF pagination
        setHasNext(!!data.next);
        setHasPrevious(!!data.previous);
        if (data.count && data.results) {
          setTotalPages(Math.ceil(data.count / 12));
        }
      }
    } catch (error) {
      setError('Failed to fetch movies');
      console.error('Error fetching movies:', error);
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
      setSearching(true);
      setSearchQuery(query);
      const response = await moviesAPI.searchMovies(query);
      setSearchResults(response.data.results || response.data);
    } catch (error) {
      setError('Search failed');
      console.error('Search error:', error);
    } finally {
      setSearching(false);
    }
  };

  const handlePageChange = (page) => {
    if (page >= 1 && page <= totalPages) {
      fetchMovies(page);
      window.scrollTo({ top: 0, behavior: 'smooth' });
    }
  };

  const handlePreviousPage = () => {
    if (hasPrevious) {
      handlePageChange(currentPage - 1);
    }
  };

  const handleNextPage = () => {
    if (hasNext) {
      handlePageChange(currentPage + 1);
    }
  };

  const displayMovies = searchQuery ? searchResults : movies;
  const isShowingSearchResults = searchQuery && searchResults.length > 0;

  return (
    <div>
      {/* Hero Section */}
      <section className="hero">    
        {/* Featured Movies Slider */}
        <MovieSlider />
      </section>

      {/* Search and Movies Section */}
      <section style={{ padding: '40px 0' }}>
        <div className="container">
          <SearchBar onSearch={handleSearch} />
          
          {error && (
            <div className="error" style={{ textAlign: 'center', marginBottom: '20px' }}>
              {error}
            </div>
          )}

          <div style={{ marginBottom: '30px' }}>
            <h2>
              {isShowingSearchResults 
                ? `Search Results for "${searchQuery}"` 
                : 'Popular Movies'
              }
            </h2>
            {isShowingSearchResults && (
              <p style={{ color: '#666' }}>
                Found {searchResults.length} movie{searchResults.length !== 1 ? 's' : ''}
              </p>
            )}
          </div>

          {(loading || searching) ? (
            <div className="loading">Loading movies...</div>
          ) : displayMovies.length > 0 ? (
            <div className="movie-grid">
              {displayMovies.map((movie) => (
                <MovieCard key={movie.id} movie={movie} />
              ))}
            </div>
          ) : (
            <div style={{ textAlign: 'center', padding: '50px', color: '#666' }}>
              {searchQuery 
                ? `No movies found for "${searchQuery}"` 
                : 'No movies available'
              }
            </div>
          )}
          
          {/* Pagination Controls - Only show for main movies, not search results */}
          {!searchQuery && movies.length > 0 && (totalPages > 1 || hasNext || hasPrevious) && (
            <div style={{
              display: 'flex',
              justifyContent: 'center',
              alignItems: 'center',
              gap: '10px',
              marginTop: '30px',
              padding: '20px'
            }}>
              <button
                onClick={handlePreviousPage}
                disabled={!hasPrevious}
                style={{
                  padding: '10px 15px',
                  border: '1px solid #ddd',
                  backgroundColor: hasPrevious ? '#007bff' : '#f8f9fa',
                  color: hasPrevious ? 'white' : '#6c757d',
                  borderRadius: '5px',
                  cursor: hasPrevious ? 'pointer' : 'not-allowed',
                  fontWeight: 'bold'
                }}
              >
                ← Previous
              </button>
              
              <span style={{
                padding: '10px 15px',
                fontWeight: 'bold',
                color: '#333'
              }}>
                Page {currentPage} of {totalPages}
              </span>
              
              <button
                onClick={handleNextPage}
                disabled={!hasNext}
                style={{
                  padding: '10px 15px',
                  border: '1px solid #ddd',
                  backgroundColor: hasNext ? '#007bff' : '#f8f9fa',
                  color: hasNext ? 'white' : '#6c757d',
                  borderRadius: '5px',
                  cursor: hasNext ? 'pointer' : 'not-allowed',
                  fontWeight: 'bold'
                }}
              >
                Next →
              </button>
            </div>
          )}

          {isAuthenticated && !searchQuery && (
            <div style={{ textAlign: 'center', marginTop: '40px' }}>
              <Link to="/dashboard" className="btn btn-primary">
                View Your Dashboard
              </Link>
            </div>
          )}
        </div>
      </section>
    </div>
  );
};

export default Home;