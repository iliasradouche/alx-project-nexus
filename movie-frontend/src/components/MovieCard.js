import React from 'react';
import { useNavigate } from 'react-router-dom';

const MovieCard = ({ movie }) => {
  const navigate = useNavigate();

  const handleClick = () => {
    navigate(`/movie/${movie.tmdb_id}`);
  };

  const formatRating = (rating) => {
    return rating ? rating.toFixed(1) : 'N/A';
  };

  const extractYear = (dateString) => {
    if (!dateString) return 'Unknown Year';
    const year = new Date(dateString).getFullYear();
    return isNaN(year) ? 'Unknown Year' : year;
  };

  const getGenreNames = (genres) => {
    if (!genres || genres.length === 0) return 'Unknown';
    return genres.map(genre => genre.name || genre).join(', ');
  };

  return (
    <div className="movie-card" onClick={handleClick}>
      <div className="movie-poster">
        {movie.poster_url ? (
          <img 
            src={movie.poster_url} 
            alt={movie.title}
            className="movie-poster"
            onError={(e) => {
              e.target.style.display = 'none';
              e.target.nextSibling.style.display = 'flex';
            }}
          />
        ) : null}
        <div 
          className="poster-placeholder"
          style={{
            display: movie.poster_url ? 'none' : 'flex',
            height: '300px',
            backgroundColor: '#f0f0f0',
            alignItems: 'center',
            justifyContent: 'center',
            fontSize: '48px',
            color: '#ccc'
          }}
        >
          🎬
        </div>
      </div>
      
      <div className="movie-info">
        <h3 className="movie-title">{movie.title}</h3>
        <p className="movie-year">{extractYear(movie.release_date)}</p>
        
        <div className="movie-details">
          <div className="movie-rating">
            <span>⭐</span>
            <span>{formatRating(movie.vote_average)}</span>
          </div>
          
          <div className="movie-genre" style={{ fontSize: '0.8rem', color: '#888', marginTop: '5px' }}>
            {getGenreNames(movie.genres)}
          </div>
        </div>
        
        {(movie.overview || movie.description) && (
          <p className="movie-description" style={{
            fontSize: '0.9rem',
            color: '#666',
            marginTop: '10px',
            overflow: 'hidden',
            display: '-webkit-box',
            WebkitLineClamp: 3,
            WebkitBoxOrient: 'vertical'
          }}>
            {movie.overview || movie.description}
          </p>
        )}
      </div>
    </div>
  );
};

export default MovieCard;