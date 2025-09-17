# Movie Recommendation Frontend

A simple React frontend for the Movie Recommendation Backend API.

## Features

- 🏠 **Home Page** - Browse popular movies and search
- 🔐 **Authentication** - User login and registration
- 📊 **Dashboard** - Personalized recommendations and watchlist
- 🎬 **Movie Details** - Detailed movie information with rating and watchlist features
- 🔍 **Search** - Find movies by title
- 📱 **Responsive Design** - Works on desktop and mobile

## Quick Start

### Prerequisites

- Node.js (v14 or higher)
- npm or yarn
- Movie Recommendation Backend running on `http://127.0.0.1:8000`

### Installation

1. Navigate to the frontend directory:
   ```bash
   cd movie-frontend
   ```

2. Install dependencies:
   ```bash
   npm install
   ```

3. Start the development server:
   ```bash
   npm start
   ```

4. Open your browser and visit `http://localhost:3000`

## Project Structure

```
src/
├── components/          # Reusable UI components
│   ├── MovieCard.js     # Movie display card
│   ├── Navbar.js        # Navigation bar
│   └── SearchBar.js     # Search input component
├── contexts/            # React contexts
│   └── AuthContext.js   # Authentication state management
├── pages/               # Page components
│   ├── Home.js          # Landing page
│   ├── Login.js         # Login page
│   ├── Register.js      # Registration page
│   ├── Dashboard.js     # User dashboard
│   └── MovieDetails.js  # Movie details page
├── services/            # API services
│   └── api.js           # Axios configuration and API calls
├── App.js               # Main app component
├── App.css              # App styles
├── index.js             # App entry point
└── index.css            # Global styles
```

## API Integration

The frontend communicates with the Django backend through:

- **Authentication**: Login, register, logout
- **Movies**: Browse, search, get details
- **User Actions**: Rate movies, manage watchlist
- **Recommendations**: Get personalized suggestions

## Available Scripts

- `npm start` - Start development server
- `npm build` - Build for production
- `npm test` - Run tests
- `npm eject` - Eject from Create React App

## Environment Variables

The app uses a proxy configuration in `package.json` to connect to the backend:

```json
"proxy": "http://127.0.0.1:8000"
```

## Deployment

### Build for Production

```bash
npm run build
```

### Deploy to Netlify/Vercel

1. Build the project
2. Upload the `build` folder
3. Set environment variables if needed

## Technologies Used

- **React 18** - UI library
- **React Router** - Client-side routing
- **Axios** - HTTP client
- **CSS3** - Styling
- **Create React App** - Build tooling

## Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Test thoroughly
5. Submit a pull request

## License

This project is part of the ALX Backend Development program.