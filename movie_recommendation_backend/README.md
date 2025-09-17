# Movie Recommendation Backend API

A comprehensive Django REST API for movie recommendations, user authentication, ratings, and watchlists. Built with Django REST Framework and integrated with The Movie Database (TMDb) API.

## 🚀 Features

- **User Authentication**: JWT-based authentication with registration, login, and token refresh
- **Movie Management**: Browse, search, and get detailed movie information
- **Personalized Recommendations**: AI-powered movie recommendations based on user preferences
- **User Ratings**: Rate movies and track your viewing history
- **Watchlist Management**: Create and manage personal movie watchlists
- **Genre Filtering**: Browse movies by genres
- **TMDb Integration**: Real-time data from The Movie Database
- **Comprehensive API Documentation**: Interactive Swagger/OpenAPI documentation

## 🛠️ Technology Stack

- **Backend Framework**: Django 5.2.6
- **API Framework**: Django REST Framework
- **Authentication**: JWT (JSON Web Tokens)
- **Database**: SQLite (development) / PostgreSQL (production)
- **External API**: The Movie Database (TMDb) API
- **Documentation**: drf-yasg (Swagger/OpenAPI)
- **Caching**: Django Cache Framework (Redis support)

## 📋 Prerequisites

- Python 3.8+
- pip (Python package manager)
- TMDb API key (free registration at https://www.themoviedb.org/)

## ⚡ Quick Start

### 1. Clone and Setup

```bash
# Navigate to the project directory
cd movie_recommendation_backend

# Install dependencies
pip install -r requirements.txt

# Apply database migrations
python manage.py migrate

# Create a superuser (optional)
python manage.py createsuperuser

# Start the development server
python manage.py runserver
```

### 2. Access the API

- **API Base URL**: `http://127.0.0.1:8000/api/movies/`
- **Interactive Documentation**: `http://127.0.0.1:8000/swagger/`
- **Alternative Documentation**: `http://127.0.0.1:8000/redoc/`
- **Admin Panel**: `http://127.0.0.1:8000/admin/`

## 🔐 Authentication

The API uses JWT (JSON Web Token) authentication. Include the token in the Authorization header:

```
Authorization: Bearer <your_jwt_token>
```

### Authentication Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/api/movies/auth/register/` | Register a new user |
| POST | `/api/movies/auth/login/` | Login and get JWT tokens |
| POST | `/api/movies/auth/logout/` | Logout (blacklist token) |
| GET | `/api/movies/auth/profile/` | Get user profile |
| POST | `/api/movies/auth/refresh/` | Refresh JWT token |

### Registration Example

```json
POST /api/movies/auth/register/
Content-Type: application/json

{
    "username": "moviefan123",
    "email": "user@example.com",
    "password": "securepassword123",
    "first_name": "John",
    "last_name": "Doe"
}
```

### Login Example

```json
POST /api/movies/auth/login/
Content-Type: application/json

{
    "username": "moviefan123",
    "password": "securepassword123"
}

# Response
{
    "access": "eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9...",
    "refresh": "eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9...",
    "user": {
        "id": 1,
        "username": "moviefan123",
        "email": "user@example.com",
        "first_name": "John",
        "last_name": "Doe"
    }
}
```

## 🎬 Movie Endpoints

### Core Movie Operations

| Method | Endpoint | Description | Auth Required |
|--------|----------|-------------|---------------|
| GET | `/api/movies/` | List all movies | No |
| GET | `/api/movies/{tmdb_id}/` | Get movie details | No |
| GET | `/api/movies/{tmdb_id}/recommendations/` | Get movie recommendations | No |
| GET | `/api/movies/genres/` | List all genres | No |

### TMDb Integration

| Method | Endpoint | Description | Auth Required |
|--------|----------|-------------|---------------|
| GET | `/api/movies/search/?query={search_term}` | Search movies | No |
| GET | `/api/movies/popular/` | Get popular movies | No |
| GET | `/api/movies/top-rated/` | Get top-rated movies | No |

### Movie Search Example

```bash
GET /api/movies/search/?query=inception

# Response
{
    "results": [
        {
            "id": 27205,
            "title": "Inception",
            "overview": "Cobb, a skilled thief who commits corporate espionage...",
            "release_date": "2010-07-16",
            "vote_average": 8.4,
            "poster_path": "/9gk7adHYeDvHkCSEqAvQNLV5Uge.jpg",
            "genre_ids": [28, 878, 53]
        }
    ],
    "total_results": 1,
    "total_pages": 1
}
```

## 👤 User Interaction Endpoints

### Ratings Management

| Method | Endpoint | Description | Auth Required |
|--------|----------|-------------|---------------|
| GET | `/api/movies/ratings/` | Get user's ratings | Yes |
| POST | `/api/movies/ratings/` | Rate a movie | Yes |
| GET | `/api/movies/ratings/{id}/` | Get specific rating | Yes |
| PUT | `/api/movies/ratings/{id}/` | Update rating | Yes |
| DELETE | `/api/movies/ratings/{id}/` | Delete rating | Yes |

### Watchlist Management

| Method | Endpoint | Description | Auth Required |
|--------|----------|-------------|---------------|
| GET | `/api/movies/watchlist/` | Get user's watchlist | Yes |
| POST | `/api/movies/watchlist/` | Add to watchlist | Yes |
| GET | `/api/movies/watchlist/{id}/` | Get watchlist item | Yes |
| DELETE | `/api/movies/watchlist/{id}/` | Remove from watchlist | Yes |
| POST | `/api/movies/user/watchlist/bulk-add/` | Bulk add to watchlist | Yes |

### Rating Example

```json
POST /api/movies/ratings/
Authorization: Bearer <your_jwt_token>
Content-Type: application/json

{
    "movie_id": 27205,
    "rating": 9,
    "review": "Amazing movie with incredible visual effects!"
}
```

### Watchlist Example

```json
POST /api/movies/watchlist/
Authorization: Bearer <your_jwt_token>
Content-Type: application/json

{
    "movie_id": 27205,
    "priority": "high",
    "notes": "Must watch this weekend"
}
```

## 📊 User Analytics Endpoints

| Method | Endpoint | Description | Auth Required |
|--------|----------|-------------|---------------|
| GET | `/api/movies/user/stats/` | Get user statistics | Yes |
| GET | `/api/movies/user/recommendations/` | Get personalized recommendations | Yes |
| GET | `/api/movies/user/movie/{movie_id}/status/` | Check movie status for user | Yes |

### User Stats Example Response

```json
GET /api/movies/user/stats/
Authorization: Bearer <your_jwt_token>

# Response
{
    "total_ratings": 45,
    "average_rating": 7.8,
    "watchlist_count": 12,
    "favorite_genres": [
        {"name": "Action", "count": 15},
        {"name": "Sci-Fi", "count": 12},
        {"name": "Drama", "count": 8}
    ],
    "recent_activity": {
        "last_rating": "2024-01-15T10:30:00Z",
        "last_watchlist_addition": "2024-01-14T15:45:00Z"
    }
}
```

## 🔍 Query Parameters

### Pagination
Most list endpoints support pagination:
- `page`: Page number (default: 1)
- `page_size`: Items per page (default: 20, max: 100)

### Filtering
- `genre`: Filter by genre ID
- `year`: Filter by release year
- `rating_gte`: Minimum rating
- `rating_lte`: Maximum rating

### Sorting
- `ordering`: Sort by field (e.g., `release_date`, `-vote_average`)

Example:
```
GET /api/movies/?genre=28&year=2023&ordering=-vote_average&page=1&page_size=10
```

## 📝 Response Format

### Success Response
```json
{
    "status": "success",
    "data": { /* response data */ },
    "message": "Operation completed successfully"
}
```

### Error Response
```json
{
    "status": "error",
    "errors": {
        "field_name": ["Error message"]
    },
    "message": "Validation failed"
}
```

### HTTP Status Codes
- `200`: Success
- `201`: Created
- `400`: Bad Request
- `401`: Unauthorized
- `403`: Forbidden
- `404`: Not Found
- `500`: Internal Server Error

## 🧪 Testing the API

### Using curl

```bash
# Register a new user
curl -X POST http://127.0.0.1:8000/api/movies/auth/register/ \
  -H "Content-Type: application/json" \
  -d '{"username":"testuser","email":"test@example.com","password":"testpass123"}'

# Login
curl -X POST http://127.0.0.1:8000/api/movies/auth/login/ \
  -H "Content-Type: application/json" \
  -d '{"username":"testuser","password":"testpass123"}'

# Get popular movies
curl -X GET http://127.0.0.1:8000/api/movies/popular/

# Rate a movie (requires authentication)
curl -X POST http://127.0.0.1:8000/api/movies/ratings/ \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer YOUR_JWT_TOKEN" \
  -d '{"movie_id":27205,"rating":9}'
```

### Using Python requests

```python
import requests

# Base URL
base_url = "http://127.0.0.1:8000/api/movies"

# Register and login
register_data = {
    "username": "testuser",
    "email": "test@example.com",
    "password": "testpass123"
}
response = requests.post(f"{base_url}/auth/register/", json=register_data)

# Login to get token
login_data = {"username": "testuser", "password": "testpass123"}
response = requests.post(f"{base_url}/auth/login/", json=login_data)
token = response.json()["access"]

# Use token for authenticated requests
headers = {"Authorization": f"Bearer {token}"}
response = requests.get(f"{base_url}/user/stats/", headers=headers)
print(response.json())
```

## 🚀 Deployment

### Environment Variables

Create a `.env` file in the project root:

```env
DEBUG=False
SECRET_KEY=your-secret-key-here
TMDB_API_KEY=your-tmdb-api-key
DATABASE_URL=postgresql://user:password@localhost:5432/moviedb
REDIS_URL=redis://localhost:6379/0
ALLOWED_HOSTS=yourdomain.com,www.yourdomain.com
```

### Production Checklist

- [ ] Set `DEBUG=False`
- [ ] Configure production database (PostgreSQL)
- [ ] Set up Redis for caching
- [ ] Configure static files serving
- [ ] Set up HTTPS
- [ ] Configure CORS settings
- [ ] Set up monitoring and logging
- [ ] Configure backup strategy

## 📚 Additional Resources

- **Interactive API Documentation**: Visit `/swagger/` when the server is running
- **TMDb API Documentation**: https://developers.themoviedb.org/3
- **Django REST Framework**: https://www.django-rest-framework.org/
- **JWT Authentication**: https://django-rest-framework-simplejwt.readthedocs.io/

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

## 📄 License

This project is licensed under the MIT License - see the LICENSE file for details.

## 🆘 Support

If you encounter any issues or have questions:

1. Check the interactive API documentation at `/swagger/`
2. Review the error messages in the API responses
3. Check the server logs for detailed error information
4. Ensure all required environment variables are set

---

**Happy coding! 🎬✨**