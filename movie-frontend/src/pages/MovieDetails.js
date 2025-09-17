import React, { useState, useEffect, useCallback } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import { moviesAPI, userAPI } from '../services/api';
import { useAuth } from '../contexts/AuthContext';

const MovieDetails = () => {
  const { id } = useParams();
  const navigate = useNavigate();
  const { isAuthenticated } = useAuth();
  const [movie, setMovie] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');
  const [userRating, setUserRating] = useState(0);
  const [isInWatchlist, setIsInWatchlist] = useState(false);
  const [actionLoading, setActionLoading] = useState(false);

  const fetchMovieDetails = useCallback(async () => {
    try {
      setLoading(true);
      setError('');
      console.log('Fetching movie details for ID:', id);
      const response = await moviesAPI.getMovie(id);
      console.log('Movie details response:', response.data);
      setMovie(response.data);
      
      // If user is authenticated, check their rating and watchlist status
      if (isAuthenticated) {
        // You might need to implement these endpoints in your API
        // For now, we'll set default values
        setUserRating(0);
        setIsInWatchlist(false);
      }
    } catch (error) {
      console.error('Movie details error:', error);
      if (error.response) {
        console.error('Error response:', error.response.data);
        console.error('Error status:', error.response.status);
        setError(`Failed to load movie details: ${error.response.status} ${error.response.statusText}`);
      } else {
        setError('Failed to load movie details');
      }
    } finally {
      setLoading(false);
    }
  }, [id, isAuthenticated]);

  useEffect(() => {
    fetchMovieDetails();
  }, [fetchMovieDetails]);

  const handleRating = async (rating) => {
    if (!isAuthenticated) {
      navigate('/login');
      return;
    }

    if (!movie || !movie.id) {
      console.error('Movie data not available');
      return;
    }

    try {
      setActionLoading(true);
      await userAPI.rateMovie(movie.id, rating);
      setUserRating(rating);
    } catch (error) {
      console.error('Rating error:', error);
    } finally {
      setActionLoading(false);
    }
  };

  const handleWatchlistToggle = async () => {
    if (!isAuthenticated) {
      navigate('/login');
      return;
    }

    if (!movie || !movie.id) {
      console.error('Movie data not available');
      return;
    }

    try {
      setActionLoading(true);
      if (isInWatchlist) {
        await userAPI.removeFromWatchlist(movie.id);
        setIsInWatchlist(false);
      } else {
        await userAPI.addToWatchlist(movie.id);
        setIsInWatchlist(true);
      }
    } catch (error) {
      console.error('Watchlist error:', error);
    } finally {
      setActionLoading(false);
    }
  };

  const formatRating = (rating) => {
    return rating ? rating.toFixed(1) : 'N/A';
  };

  const getGenreNames = (genres) => {
    if (!genres || genres.length === 0) return 'Unknown';
    return genres.map(genre => genre.name || genre).join(', ');
  };

  if (loading) {
    return <div className="loading">Loading movie details...</div>;
  }

  if (error) {
    return (
      <div className="container" style={{ textAlign: 'center', paddingTop: '50px' }}>
        <div className="error">{error}</div>
        <button onClick={() => navigate(-1)} className="btn btn-secondary" style={{ marginTop: '20px' }}>
          Go Back
        </button>
      </div>
    );
  }

  if (!movie) {
    return (
      <div className="container" style={{ textAlign: 'center', paddingTop: '50px' }}>
        <p>Movie not found</p>
        <button onClick={() => navigate(-1)} className="btn btn-secondary">
          Go Back
        </button>
      </div>
    );
  }

  return (
    <div className="container" style={{ paddingTop: '20px' }}>
      <button 
        onClick={() => navigate(-1)} 
        className="btn btn-secondary"
        style={{ marginBottom: '20px' }}
      >
        ← Back
      </button>

      <div style={{ display: 'flex', gap: '30px', flexWrap: 'wrap' }}>
        {/* Movie Poster */}
        <div style={{ flex: '0 0 300px' }}>
          {movie.poster_url ? (
            <img 
              src={movie.poster_url} 
              alt={movie.title}
              style={{ width: '100%', borderRadius: '10px', boxShadow: '0 4px 8px rgba(0,0,0,0.1)' }}
            />
          ) : (
            <div style={{
              width: '100%',
              height: '450px',
              backgroundColor: '#f0f0f0',
              borderRadius: '10px',
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'center',
              fontSize: '48px',
              color: '#ccc'
            }}>
              🎬
            </div>
          )}
        </div>

        {/* Movie Info */}
        <div style={{ flex: '1', minWidth: '300px' }}>
          <h1 style={{ marginBottom: '10px' }}>{movie.title}</h1>
          
          <div style={{ marginBottom: '20px', color: '#666' }}>
            <p><strong>Year:</strong> {movie.release_year || 'Unknown'}</p>
            <p><strong>Genres:</strong> {getGenreNames(movie.genres)}</p>
            <p><strong>Rating:</strong> ⭐ {formatRating(movie.average_rating)}</p>
          </div>

          {movie.description && (
            <div style={{ marginBottom: '30px' }}>
              <h3>Description</h3>
              <p style={{ lineHeight: '1.6', color: '#555' }}>{movie.description}</p>
            </div>
          )}

          {/* User Actions */}
          {isAuthenticated && (
            <div style={{ marginBottom: '30px' }}>
              <h3>Your Actions</h3>
              
              {/* Rating */}
              <div style={{ marginBottom: '20px' }}>
                <p style={{ marginBottom: '10px' }}>Rate this movie:</p>
                <div style={{ display: 'flex', gap: '5px' }}>
                  {[1, 2, 3, 4, 5].map((star) => (
                    <button
                      key={star}
                      onClick={() => handleRating(star)}
                      disabled={actionLoading}
                      style={{
                        background: 'none',
                        border: 'none',
                        fontSize: '24px',
                        cursor: 'pointer',
                        color: star <= userRating ? '#f39c12' : '#ddd'
                      }}
                    >
                      ⭐
                    </button>
                  ))}
                </div>
                {userRating > 0 && (
                  <p style={{ fontSize: '14px', color: '#666', marginTop: '5px' }}>
                    You rated this movie {userRating} star{userRating !== 1 ? 's' : ''}
                  </p>
                )}
              </div>

              {/* Watchlist */}
              <button
                onClick={handleWatchlistToggle}
                disabled={actionLoading}
                className={`btn ${isInWatchlist ? 'btn-secondary' : 'btn-primary'}`}
              >
                {actionLoading ? 'Loading...' : (
                  isInWatchlist ? '✓ Remove from Watchlist' : '+ Add to Watchlist'
                )}
              </button>
            </div>
          )}

          {!isAuthenticated && (
            <div style={{ padding: '20px', backgroundColor: '#f8f9fa', borderRadius: '8px' }}>
              <p style={{ marginBottom: '15px' }}>Sign in to rate movies and add them to your watchlist!</p>
              <button 
                onClick={() => navigate('/login')} 
                className="btn btn-primary"
              >
                Sign In
              </button>
            </div>
          )}
        </div>
      </div>
    </div>
  );
};

export default MovieDetails;