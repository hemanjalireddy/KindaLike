# KindaLike - Restaurant Recommender Chatbot

A niche-based restaurant recommendation system that uses user preferences to provide personalized restaurant suggestions through a chatbot interface.

## Project Overview

KindaLike is a full-stack web application with a React frontend and Python (FastAPI) backend. It collects detailed user preferences through an interactive survey and stores them in a PostgreSQL database for personalized restaurant recommendations.

## Features

### Frontend
- **User Authentication**
  - Signup and Login with JWT tokens
  - Secure password handling
  - Form validation

- **Preference Survey**
  - Multi-step survey (5 categories)
  - Radio button interface
  - Progress tracking
  - Categories: Cuisine Type, Price Range, Dining Style, Dietary Restrictions, Atmosphere

- **Modern UI**
  - Responsive design
  - Gradient styling with smooth animations
  - Mobile-friendly interface

### Backend
- **RESTful API** built with FastAPI
- **PostgreSQL Database** with Docker
- **JWT Authentication**
- **Password Hashing** with bcrypt
- **CORS enabled** for frontend communication
- **Persistent data storage** using Docker volumes
- **Poetry** for dependency management

## Tech Stack

**Frontend:**
- React + Vite
- React Router
- CSS3

**Backend:**
- Python 3.10+
- FastAPI
- PostgreSQL
- psycopg2
- bcrypt
- JWT
- Poetry (package manager)

**Infrastructure:**
- Docker & Docker Compose
- Docker Volumes (persistent storage)

## Project Structure

```
KindaLike/
├── src/                      # Frontend React code
│   ├── pages/
│   │   ├── Login.jsx
│   │   ├── Signup.jsx
│   │   └── Survey.jsx
│   ├── App.jsx
│   ├── App.css
│   └── main.jsx
├── backend/                  # Python FastAPI backend
│   ├── app/
│   │   ├── routes/
│   │   │   ├── auth.py      # Authentication endpoints
│   │   │   └── preferences.py # Preferences endpoints
│   │   ├── models/
│   │   │   └── schemas.py   # Pydantic models
│   │   ├── database.py      # PostgreSQL connection
│   │   ├── utils.py         # Password hashing, JWT
│   │   └── main.py          # FastAPI app
│   ├── pyproject.toml       # Poetry configuration
│   ├── poetry.lock          # Locked dependencies
│   └── README.md            # Backend documentation
├── database/
│   └── init.sql            # Database schema
├── docker-compose.yml       # PostgreSQL container config
├── .env                     # Environment variables
├── .env.example            # Environment template
├── index.html
├── vite.config.js
└── package.json
```

## Getting Started

### Prerequisites
- Node.js (v14+)
- Python 3.10+
- Docker & Docker Compose
- Poetry (Python package manager)
- npm or yarn

### Installation

#### 1. Clone the repository
```bash
git clone https://github.com/hemanjalireddy/KindaLike.git
cd KindaLike
```

#### 2. Set up the Database

Start PostgreSQL using Docker:
```bash
docker-compose up -d
```

This creates:
- PostgreSQL database named `kindalike`
- Tables: `users` and `user_preferences`
- Persistent volume for data storage

To check database status:
```bash
docker-compose ps
```

#### 3. Set up the Backend

**Install Poetry (if not already installed):**

Windows (PowerShell):
```powershell
(Invoke-WebRequest -Uri https://install.python-poetry.org -UseBasicParsing).Content | py -
```

macOS/Linux:
```bash
curl -sSL https://install.python-poetry.org | python3 -
```

**Install Python dependencies:**
```bash
cd backend
poetry install
```

Update `.env` if needed (default password: `kindalike123`):
```env
DB_USER=postgres
DB_HOST=localhost
DB_NAME=kindalike
DB_PASSWORD=kindalike123
DB_PORT=5432
PORT=5000
JWT_SECRET=kindalike_secret_key_2024
```

**Start the backend server:**
```bash
poetry run python -m app.main
```

Or activate the virtual environment first:
```bash
poetry shell
python -m app.main
```

The API will be available at `http://localhost:5000`

API Documentation: `http://localhost:5000/docs`

#### 4. Set up the Frontend

Install frontend dependencies:
```bash
# From project root
npm install
```

Start the frontend:
```bash
npm run dev
```

The app will be available at `http://localhost:5173`

## API Endpoints

### Authentication
- `POST /api/auth/signup` - Register new user
- `POST /api/auth/login` - Login user

### Preferences (requires authentication)
- `POST /api/preferences/` - Create/update preferences
- `GET /api/preferences/` - Get user preferences

See `backend/README.md` for detailed API documentation.

## Database Persistence

Your data is stored in a Docker volume named `postgres_data`:

✅ Data persists when container stops
✅ Data persists after system restart
✅ Data persists when container is recreated

To remove data permanently:
```bash
docker-compose down -v
```

## Development

### Frontend Development
```bash
npm run dev          # Start dev server with hot reload
npm run build        # Build for production
npm run preview      # Preview production build
```

### Backend Development
```bash
cd backend
poetry run python -m app.main   # Start with auto-reload
```

Or:
```bash
cd backend
poetry shell         # Activate virtual environment
python -m app.main   # Run the server
```

### Poetry Commands
```bash
poetry install       # Install dependencies
poetry add package   # Add new dependency
poetry update        # Update dependencies
poetry show          # Show installed packages
poetry shell         # Activate virtual environment
```

## How It Works

1. **User Registration**: Creates account, password is hashed with bcrypt
2. **User Login**: Validates credentials, returns JWT token
3. **Survey**: User fills out preferences (5 steps)
4. **Save Preferences**: Frontend sends preferences to backend with JWT
5. **Database Storage**: Preferences saved to PostgreSQL
6. **Persistence**: Data remains even after restart

## What to Push to GitHub

**Include:**
- Source code (`src/`, `backend/`)
- Configuration files (`pyproject.toml`, `poetry.lock`)
- Documentation
- `.gitignore`
- `docker-compose.yml`
- `.env.example` (template)

**Exclude (in .gitignore):**
- `node_modules/`
- `backend/.venv/`
- `.env` (contains secrets!)
- `__pycache__/`
- `dist/`

## Future Enhancements

- [ ] Chatbot integration with AI/NLP
- [ ] Restaurant database/API integration
- [ ] Recommendation algorithm
- [ ] User dashboard
- [ ] Update preferences feature
- [ ] Restaurant favorites
- [ ] Location-based recommendations

## Troubleshooting

**Database won't start:**
```bash
docker-compose logs postgres
```

**Port conflicts:**
Change ports in `docker-compose.yml` or `.env`

**Backend can't connect to database:**
Make sure Docker container is running: `docker-compose ps`

**Poetry issues:**
```bash
poetry env remove python
poetry install
```

## License

ISC

## Author

Hemanjali Reddy

## Repository

https://github.com/hemanjalireddy/KindaLike
