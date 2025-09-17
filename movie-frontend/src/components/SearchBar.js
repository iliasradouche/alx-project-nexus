import React, { useState } from 'react';

const SearchBar = ({ onSearch, placeholder = "Search for movies..." }) => {
  const [query, setQuery] = useState('');

  const handleSubmit = (e) => {
    e.preventDefault();
    if (query.trim()) {
      onSearch(query.trim());
    }
  };

  const handleChange = (e) => {
    setQuery(e.target.value);
    // Optional: Real-time search with debouncing
    // You can implement debouncing here if needed
  };

  const handleClear = () => {
    setQuery('');
    onSearch(''); // Clear search results
  };

  return (
    <div className="search-bar">
      <form onSubmit={handleSubmit} style={{ position: 'relative' }}>
        <input
          type="text"
          value={query}
          onChange={handleChange}
          placeholder={placeholder}
          className="search-input"
        />
        
        {query && (
          <button
            type="button"
            onClick={handleClear}
            style={{
              position: 'absolute',
              right: '50px',
              top: '50%',
              transform: 'translateY(-50%)',
              background: 'none',
              border: 'none',
              fontSize: '18px',
              cursor: 'pointer',
              color: '#999'
            }}
          >
            ✕
          </button>
        )}
        
        <button
          type="submit"
          style={{
            position: 'absolute',
            right: '15px',
            top: '50%',
            transform: 'translateY(-50%)',
            background: 'none',
            border: 'none',
            fontSize: '18px',
            cursor: 'pointer',
            color: '#007bff'
          }}
        >
          🔍
        </button>
      </form>
    </div>
  );
};

export default SearchBar;