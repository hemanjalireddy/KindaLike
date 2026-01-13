# KindaLike Backend API

Python FastAPI backend for the KindaLike restaurant recommender system.

## Setup Instructions

### Prerequisites
- Python 3.10+
- Docker and Docker Compose
- Poetry (Python package manager)

### Install Poetry

If you don't have Poetry installed:

**Windows (PowerShell):**
```powershell
(Invoke-WebRequest -Uri https://install.python-poetry.org -UseBasicParsing).Content | py -
```

**macOS/Linux:**
```bash
curl -sSL https://install.python-poetry.org | python3 -
```

Verify installation:
```bash
poetry --version
```

### 1. Start PostgreSQL Database

First, start the PostgreSQL database using Docker:

```bash
# From the project root directory
docker-compose up -d
```

This will:
- Start a PostgreSQL container
- Create the `kindalike` database
- Run the initialization script to create tables
- Data is persisted in a Docker volume named `postgres_data`

**Important**: Even if you stop or remove the container, your data will persist in the volume!

To check if the database is running:
```bash
docker-compose ps
```

To stop the database:
```bash
docker-compose down
```

To stop AND remove the data (careful!):
```bash
docker-compose down -v
```

### 2. Install Python Dependencies with Poetry

```bash
cd backend
poetry install
```

This will:
- Create a virtual environment automatically (in `.venv/`)
- Install all dependencies from `pyproject.toml`
- Generate/update `poetry.lock` for reproducible builds

### 3. Configure Environment Variables

The `.env` file in the project root contains the database configuration:

```
DB_USER=postgres
DB_HOST=localhost
DB_NAME=kindalike
DB_PASSWORD=kindalike123
DB_PORT=5432
PORT=5000
JWT_SECRET=kindalike_secret_key_2024
```

### 4. Run the Backend Server

**Using Poetry:**
```bash
cd backend
poetry run python -m app.main
```

**Or activate the virtual environment first:**
```bash
cd backend
poetry shell
python -m app.main
```

**Or using uvicorn directly:**
```bash
poetry run uvicorn app.main:app --reload --port 5000
```

The API will be available at: `http://localhost:5000`

### API Documentation

Once the server is running, visit:
- Swagger UI: `http://localhost:5000/docs`
- ReDoc: `http://localhost:5000/redoc`

## Poetry Commands

### Common Commands
```bash
# Install dependencies
poetry install

# Add a new dependency
poetry add package-name

# Add a development dependency
poetry add --group dev package-name

# Update dependencies
poetry update

# Show installed packages
poetry show

# Activate virtual environment
poetry shell

# Run a command in the virtual environment
poetry run python script.py

# Export to requirements.txt (if needed)
poetry export -f requirements.txt --output requirements.txt
```

## API Endpoints

### Authentication

#### POST `/api/auth/signup`
Register a new user
```json
{
  "username": "testuser",
  "password": "password123"
}
```

Response:
```json
{
  "access_token": "eyJ...",
  "token_type": "bearer",
  "user": {
    "id": 1,
    "username": "testuser",
    "created_at": "2024-01-12T10:30:00"
  }
}
```

#### POST `/api/auth/login`
Login existing user
```json
{
  "username": "testuser",
  "password": "password123"
}
```

### User Preferences

#### POST `/api/preferences/`
Create or update user preferences (requires authentication)

Headers:
```
Authorization: Bearer <token>
```

Body:
```json
{
  "cuisine_type": "Italian",
  "price_range": "moderate",
  "dining_style": "dine-in",
  "dietary_restrictions": "None",
  "atmosphere": "casual"
}
```

#### GET `/api/preferences/`
Get user preferences (requires authentication)

Headers:
```
Authorization: Bearer <token>
```

## Database Schema

### users table
- `id` (SERIAL PRIMARY KEY)
- `username` (VARCHAR UNIQUE)
- `password_hash` (VARCHAR)
- `created_at` (TIMESTAMP)

### user_preferences table
- `id` (SERIAL PRIMARY KEY)
- `user_id` (INTEGER FOREIGN KEY)
- `cuisine_type` (VARCHAR)
- `price_range` (VARCHAR)
- `dining_style` (VARCHAR)
- `dietary_restrictions` (VARCHAR)
- `atmosphere` (VARCHAR)
- `created_at` (TIMESTAMP)
- `updated_at` (TIMESTAMP)

## Docker Volume Persistence

Your database data is stored in a Docker volume called `postgres_data`. This means:

✅ Data persists when you stop the container
✅ Data persists when you restart your computer
✅ Data persists even if you delete and recreate the container

❌ Data is ONLY deleted if you run `docker-compose down -v`

To see your volumes:
```bash
docker volume ls
```

To inspect the volume:
```bash
docker volume inspect kindalike_postgres_data
```

## Development

The backend uses FastAPI with automatic reloading enabled. Any changes to Python files will automatically restart the server.

### Project Structure
```
backend/
├── app/
│   ├── __init__.py
│   ├── main.py              # FastAPI app
│   ├── database.py          # PostgreSQL connection
│   ├── utils.py             # Password hashing, JWT
│   ├── models/
│   │   └── schemas.py       # Pydantic models
│   └── routes/
│       ├── auth.py          # Authentication endpoints
│       └── preferences.py   # Preferences endpoints
├── pyproject.toml           # Poetry configuration
├── poetry.lock              # Locked dependencies
└── README.md
```

## Troubleshooting

### Cannot connect to database
1. Check if Docker is running: `docker ps`
2. Check if PostgreSQL container is up: `docker-compose ps`
3. Restart the database: `docker-compose restart`

### Port already in use
If port 5000 or 5432 is already in use, modify the ports in `docker-compose.yml` or `.env`

### Database connection refused
Make sure the database is fully initialized. Check logs:
```bash
docker-compose logs postgres
```

### Poetry virtual environment issues
If you have issues with the virtual environment:
```bash
# Remove the venv and reinstall
poetry env remove python
poetry install
```

### Python version issues
Make sure you have Python 3.10 or higher:
```bash
python --version
```

If needed, tell Poetry which Python to use:
```bash
poetry env use python3.10
```
