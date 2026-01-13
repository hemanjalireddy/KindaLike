# KindaLike - Complete Setup Guide

This guide will walk you through setting up the entire KindaLike application from scratch.

## Prerequisites

Install these first:
- **Node.js** (v14+): https://nodejs.org/
- **Python** (3.10+): https://www.python.org/downloads/
- **Docker Desktop**: https://www.docker.com/products/docker-desktop/
- **Poetry**: https://python-poetry.org/docs/#installation

### Install Poetry (Windows PowerShell):
```powershell
(Invoke-WebRequest -Uri https://install.python-poetry.org -UseBasicParsing).Content | py -
```

### Verify installations:
```bash
node --version
python --version
docker --version
poetry --version
```

---

## Step-by-Step Setup

### 1. Clone the Repository

```bash
git clone https://github.com/hemanjalireddy/KindaLike.git
cd KindaLike
```

---

### 2. Set Up PostgreSQL Database with Docker

**Start the PostgreSQL container:**
```bash
docker-compose up -d
```

This command:
- Downloads PostgreSQL 15 Alpine image
- Creates a container named `kindalike_db`
- Creates the `kindalike` database
- Runs `database/init.sql` to create tables
- Creates a persistent Docker volume `postgres_data`

**Verify the database is running:**
```bash
docker-compose ps
```

You should see:
```
NAME            IMAGE                PORTS
kindalike_db    postgres:15-alpine   0.0.0.0:5432->5432/tcp
```

**Check database logs:**
```bash
docker-compose logs postgres
```

---

### 3. Set Up the Backend (Python + FastAPI)

**Navigate to backend directory:**
```bash
cd backend
```

**Install Python dependencies with Poetry:**
```bash
poetry install
```

This will:
- Create a virtual environment at `backend/.venv/`
- Install all dependencies from `pyproject.toml`
- Generate `poetry.lock` for reproducible builds

**Configure environment variables:**

The `.env` file in the project root should contain:
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

Option 1 - Using Poetry:
```bash
poetry run python -m app.main
```

Option 2 - Activate venv first:
```bash
poetry shell
python -m app.main
```

The API should start at: **http://localhost:5000**

**Verify backend is running:**
- Visit: http://localhost:5000 (should show "Welcome to KindaLike API")
- Visit: http://localhost:5000/docs (Swagger API documentation)
- Visit: http://localhost:5000/health (should return {"status": "healthy"})

---

### 4. Set Up the Frontend (React + Vite)

**Open a NEW terminal** (keep backend running in the first terminal)

**Navigate to project root:**
```bash
cd /path/to/KindaLike
```

**Install frontend dependencies:**
```bash
npm install
```

**Start the frontend dev server:**
```bash
npm run dev
```

The frontend should start at: **http://localhost:5173**

---

## Testing the Application

### Test User Registration:
1. Visit http://localhost:5173
2. Click "Sign up here"
3. Create a new account (username: testuser, password: password123)
4. You should be redirected to the survey

### Test Survey:
1. Fill out all 5 steps of the survey
2. Click "Complete Profile"
3. Check browser console - you should see "Preferences saved:"
4. Check backend logs - you should see the database save operation

### Test Login:
1. Logout (clear browser localStorage or open incognito)
2. Visit http://localhost:5173/login
3. Login with your credentials
4. You should be redirected to the survey

---

## Viewing the Database

### Option 1: Using psql Command Line

**Connect to the database:**
```bash
docker exec -it kindalike_db psql -U postgres -d kindalike
```

**Useful psql commands:**
```sql
-- List all tables
\dt

-- View users table
SELECT * FROM users;

-- View user_preferences table
SELECT * FROM user_preferences;

-- View users with their preferences (JOIN)
SELECT u.username, p.cuisine_type, p.price_range, p.dining_style, p.dietary_restrictions, p.atmosphere
FROM users u
LEFT JOIN user_preferences p ON u.id = p.user_id;

-- Exit psql
\q
```

### Option 2: Using DBeaver (GUI)

1. Download DBeaver: https://dbeaver.io/download/
2. Install and open DBeaver
3. Click "New Database Connection"
4. Select PostgreSQL
5. Enter connection details:
   - Host: `localhost`
   - Port: `5432`
   - Database: `kindalike`
   - Username: `postgres`
   - Password: `kindalike123`
6. Click "Test Connection" then "Finish"
7. Expand the connection tree to browse tables

### Option 3: Using pgAdmin (GUI)

1. Download pgAdmin: https://www.pgadmin.org/download/
2. Install and open pgAdmin
3. Right-click "Servers" → "Register" → "Server"
4. General tab: Name: `KindaLike`
5. Connection tab:
   - Host: `localhost`
   - Port: `5432`
   - Database: `kindalike`
   - Username: `postgres`
   - Password: `kindalike123`
6. Save and connect
7. Navigate to: Servers → KindaLike → Databases → kindalike → Schemas → public → Tables

---

## Understanding the Virtual Environment

### Where is the venv?

Poetry automatically created a virtual environment at:
```
backend/.venv/
```

**On Windows:**
- `backend/.venv/Scripts/activate.bat` (Command Prompt)
- `backend/.venv/Scripts/Activate.ps1` (PowerShell)
- `backend/.venv/Scripts/python.exe` (Python executable)

**On Mac/Linux:**
- `backend/.venv/bin/activate` (Bash/Zsh)
- `backend/.venv/bin/python` (Python executable)

### How to activate the venv manually:

**Windows (PowerShell):**
```powershell
cd backend
.venv\Scripts\Activate.ps1
```

**Windows (Command Prompt):**
```cmd
cd backend
.venv\Scripts\activate.bat
```

**Mac/Linux:**
```bash
cd backend
source .venv/bin/activate
```

### How to deactivate:
```bash
deactivate
```

### Poetry manages venv automatically:
You don't need to activate manually if you use:
```bash
poetry shell    # Activates venv
poetry run python -m app.main    # Runs command in venv
```

---

## Database Persistence

### Where is the data stored?

Your PostgreSQL data is stored in a Docker volume named `postgres_data`. This is NOT inside the container itself.

**View all Docker volumes:**
```bash
docker volume ls
```

**Inspect the volume:**
```bash
docker volume inspect kindalike_postgres_data
```

### What persists?

✅ **Data persists when:**
- You stop the container (`docker-compose down`)
- You restart your computer
- You rebuild the container
- You update the PostgreSQL image

❌ **Data is DELETED when:**
- You run `docker-compose down -v` (the `-v` flag removes volumes)
- You manually delete the volume: `docker volume rm kindalike_postgres_data`

### Backup the database:

**Export database to file:**
```bash
docker exec kindalike_db pg_dump -U postgres kindalike > backup.sql
```

**Restore from backup:**
```bash
docker exec -i kindalike_db psql -U postgres kindalike < backup.sql
```

---

## Common Commands

### Docker Commands:
```bash
# Start database
docker-compose up -d

# Stop database (data persists!)
docker-compose down

# Stop database AND delete data (careful!)
docker-compose down -v

# View logs
docker-compose logs -f postgres

# Restart database
docker-compose restart

# Check status
docker-compose ps
```

### Poetry Commands:
```bash
# Install dependencies
poetry install

# Add new package
poetry add package-name

# Add dev dependency
poetry add --group dev package-name

# Update dependencies
poetry update

# Show installed packages
poetry show

# Activate virtual environment
poetry shell

# Run command in venv
poetry run python script.py

# Exit virtual environment
exit  # or Ctrl+D
```

### Frontend Commands:
```bash
# Start dev server
npm run dev

# Build for production
npm run build

# Preview production build
npm run preview

# Install new package
npm install package-name
```

---

## Troubleshooting

### Frontend can't connect to backend:
**Error:** "Failed to fetch" or CORS errors

**Solution:**
1. Make sure backend is running: http://localhost:5000/health
2. Check if port 5000 is in use by another app
3. Check browser console for errors
4. Verify CORS settings in `backend/app/main.py`

### Database connection refused:
**Error:** "Connection refused" or "could not connect to server"

**Solution:**
1. Check if Docker is running: `docker ps`
2. Check if PostgreSQL container is up: `docker-compose ps`
3. Check logs: `docker-compose logs postgres`
4. Restart: `docker-compose restart`
5. Verify port 5432 is not used by another app

### Poetry venv not found:
**Error:** "No virtualenv has been activated"

**Solution:**
```bash
cd backend
poetry env info  # Check venv status
poetry install   # Reinstall if needed
poetry shell     # Activate venv
```

### Port already in use:
**Error:** "Port 5000 is already in use" or "Port 5432 is already in use"

**Solution:**
1. Find what's using the port (Windows):
   ```powershell
   netstat -ano | findstr :5000
   ```
2. Kill the process or change the port in `.env` or `docker-compose.yml`

### Python version issues:
**Error:** "Requires Python >=3.10"

**Solution:**
```bash
python --version  # Check your version
poetry env use python3.10  # Tell Poetry which Python to use
poetry install  # Reinstall
```

---

## Architecture Overview

```
┌─────────────────────────────────────────────────────────────┐
│                         Browser                             │
│                  http://localhost:5173                      │
│                    (React Frontend)                         │
└────────────────────────┬────────────────────────────────────┘
                         │
                         │ HTTP Requests (fetch)
                         │
┌────────────────────────▼────────────────────────────────────┐
│                   Python Backend                            │
│                http://localhost:5000                        │
│                  (FastAPI REST API)                         │
│                                                             │
│  Routes:                                                    │
│  - POST /api/auth/signup                                   │
│  - POST /api/auth/login                                    │
│  - POST /api/preferences/                                  │
│  - GET  /api/preferences/                                  │
└────────────────────────┬────────────────────────────────────┘
                         │
                         │ SQL Queries (psycopg2)
                         │
┌────────────────────────▼────────────────────────────────────┐
│              PostgreSQL Database                            │
│                  (Docker Container)                         │
│                localhost:5432/kindalike                     │
│                                                             │
│  Tables:                                                    │
│  - users (id, username, password_hash, created_at)        │
│  - user_preferences (id, user_id, cuisine_type, ...)     │
└────────────────────────┬────────────────────────────────────┘
                         │
                         │ Persistent Storage
                         │
┌────────────────────────▼────────────────────────────────────┐
│                   Docker Volume                             │
│                  postgres_data                              │
│            (Survives container restarts)                    │
└─────────────────────────────────────────────────────────────┘
```

---

## Next Steps

Now that everything is set up, you can:
1. Test the complete user flow (signup → survey → database)
2. View data in the database using psql or DBeaver
3. Start building the chatbot integration
4. Add more API endpoints
5. Enhance the frontend UI

## Need Help?

- Backend API docs: http://localhost:5000/docs
- Check logs: `docker-compose logs` and check terminal running backend
- Read README.md in project root
- Read backend/README.md for API details
