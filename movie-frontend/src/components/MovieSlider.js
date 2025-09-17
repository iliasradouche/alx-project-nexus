import React, { useState, useEffect } from 'react';
import { moviesAPI } from '../services/api';
import './MovieSlider.css';

const MovieSlider = () => {
  const [movies, setMovies] = useState([]);
  const [currentIndex, setCurrentIndex] = useState(0);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');

  useEffect(() => {
    fetchPopularMovies();
  }, []);

  const fetchPopularMovies = async () => {
    try {
      setLoading(true);
      const response = await moviesAPI.getMovies({ page_size: 10, page: 1 });
      const data = response.data;
      setMovies(data.results || data);
    } catch (error) {
      setError('Failed to fetch movies');
      console.error('Error fetching movies:', error);
    } finally {
      setLoading(false);
    }
  };

  const nextSlide = () => {
    setCurrentIndex((prevIndex) => 
      prevIndex === movies.length - 1 ? 0 : prevIndex + 1
    );
  };

  const prevSlide = () => {
    setCurrentIndex((prevIndex) => 
      prevIndex === 0 ? movies.length - 1 : prevIndex - 1
    );
  };

  const goToSlide = (index) => {
    setCurrentIndex(index);
  };

  // Auto-slide functionality
  useEffect(() => {
    if (movies.length > 0) {
      const interval = setInterval(nextSlide, 5000); // Change slide every 5 seconds
      return () => clearInterval(interval);
    }
  }, [movies.length]);

  const extractYear = (dateString) => {
    if (!dateString) return 'Unknown Year';
    return new Date(dateString).getFullYear();
  };

  if (loading) {
    return (
      <div className="movie-slider loading">
        <div className="slider-loading">Loading featured movies...</div>
      </div>
    );
  }

  if (error || movies.length === 0) {
    return (
      <div className="movie-slider error">
        <div className="slider-error">{error || 'No movies available'}</div>
      </div>
    );
  }

  const currentMovie = movies[currentIndex];

  return (
    <div className="movie-slider">
      <div className="slider-container">
        <div className="slide active">
          <div className="slide-background">
            {currentMovie.poster_path ? (
              <img 
                src={`https://image.tmdb.org/t/p/w1280${currentMovie.poster_path}`}
                alt={currentMovie.title}
                className="slide-bg-image"
              />
            ) : (
              <div className="slide-bg-placeholder"></div>
            )}
            <div className="slide-overlay"></div>
          </div>
          
          <div className="slide-content">
            <div className="slide-info">
              <h2 className="slide-title">{currentMovie.title}</h2>
              <div className="slide-meta">
                <span className="slide-year">{extractYear(currentMovie.release_date)}</span>
                {currentMovie.vote_average && (
                  <span className="slide-rating">
                    ⭐ {currentMovie.vote_average.toFixed(1)}
                  </span>
                )}
              </div>
              <p className="slide-overview">
                {currentMovie.overview && currentMovie.overview.length > 200
                  ? `${currentMovie.overview.substring(0, 200)}...`
                  : currentMovie.overview || 'No description available.'}
              </p>
              <div className="slide-actions">
                <button className="btn btn-primary">Watch Now</button>
                <button className="btn btn-secondary">Add to Watchlist</button>
              </div>
            </div>
          </div>
        </div>

        {/* Navigation Arrows */}
        <button className="slider-nav prev" onClick={prevSlide}>
          ❮
        </button>
        <button className="slider-nav next" onClick={nextSlide}>
          ❯
        </button>

        {/* Dots Indicator */}
        <div className="slider-dots">
          {movies.map((_, index) => (
            <button
              key={index}
              className={`dot ${index === currentIndex ? 'active' : ''}`}
              onClick={() => goToSlide(index)}
            ></button>
          ))}
        </div>
      </div>
    </div>
  );
};

export default MovieSlider;