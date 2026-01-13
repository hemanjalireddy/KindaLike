# Docker Deployment Guide

This guide explains how to run the entire KindaLike application (database, backend, frontend) using Docker Compose with a single command.

## Prerequisites

- **Docker Desktop** installed and running
- No other services using ports 80, 5000, or 5432

## Quick Start - Run Everything with One Command

### Start All Services:

```bash
docker-compose up -d
```

That's it! This single command will:
1. ✅ Build the frontend Docker image
2. ✅ Build the backend Docker image
3. ✅ Pull the PostgreSQL image
4. ✅ Create the database and run init.sql
5. ✅ Start all three services
6. ✅ Set up networking between them

### Access the Application:

- **Frontend**: http://localhost (port 80)
- **Backend API**: http://localhost:5000
- **API Docs**: http://localhost:5000/docs
- **Database**: localhost:5432

## What's Running?

After `docker-compose up -d`, you have 3 containers:

| Container | Service | Port | Description |
|-----------|---------|------|-------------|
| `kindalike_frontend` | React + Nginx | 80 | Web interface |
| `kindalike_backend` | Python FastAPI | 5000 | REST API |
| `kindalike_db` | PostgreSQL 15 | 5432 | Database |

## Common Commands

### View Running Containers:
```bash
docker-compose ps
```

### View Logs:
```bash
# All services
docker-compose logs -f

# Specific service
docker-compose logs -f frontend
docker-compose logs -f backend
docker-compose logs -f postgres
```

### Stop All Services:
```bash
docker-compose down
```

**Note:** This stops containers but **keeps your data** (PostgreSQL volume persists)

### Stop and Remove Data:
```bash
docker-compose down -v
```

**⚠️ Warning:** This deletes all database data!

### Rebuild After Code Changes:
```bash
# Rebuild all
docker-compose up -d --build

# Rebuild specific service
docker-compose up -d --build frontend
docker-compose up -d --build backend
```

### Restart Services:
```bash
# Restart all
docker-compose restart

# Restart specific service
docker-compose restart backend
```

## Architecture

```
┌─────────────────────────────────────────────────────┐
│  Browser (http://localhost)                         │
└────────────┬────────────────────────────────────────┘
             │
             ▼
┌─────────────────────────────────────────────────────┐
│  Nginx (Frontend Container)                         │
│  - Serves React app                                 │
│  - Proxies /api/* to backend                        │
│  Port: 80                                           │
└────────────┬────────────────────────────────────────┘
             │
             ▼ (API requests)
┌─────────────────────────────────────────────────────┐
│  FastAPI (Backend Container)                        │
│  - Python backend                                   │
│  - Handles authentication & preferences             │
│  Port: 5000                                         │
└────────────┬────────────────────────────────────────┘
             │
             ▼ (SQL queries)
┌─────────────────────────────────────────────────────┐
│  PostgreSQL (Database Container)                    │
│  - Stores users & preferences                       │
│  - Data persists in Docker volume                   │
│  Port: 5432                                         │
└─────────────────────────────────────────────────────┘
```

## How It Works

### Frontend Container:
- **Stage 1**: Builds React app with Node.js
- **Stage 2**: Serves static files with Nginx
- Nginx proxies `/api/*` requests to backend
- Production-optimized (multi-stage build)

### Backend Container:
- Uses Python 3.10
- Installs dependencies with Poetry
- Connects to `postgres` container (not `localhost`)
- Auto-reloads on code changes

### Database Container:
- PostgreSQL 15 Alpine (lightweight)
- Runs `database/init.sql` on first start
- Data stored in Docker volume `postgres_data`

## Networking

All containers are on the same Docker network: `kindalike-network`

**Container DNS:**
- Backend connects to database via hostname: `postgres`
- Frontend proxies to backend via hostname: `backend`

**From your computer:**
- Access frontend: `localhost:80`
- Access backend: `localhost:5000`
- Access database: `localhost:5432`

## Development vs Production

### Development (Local):
```bash
# Frontend
npm run dev  # http://localhost:5173

# Backend
cd backend
poetry run python -m app.main  # http://localhost:5000

# Database
docker-compose up postgres -d
```

**API calls:** Frontend calls `http://localhost:5000/api/*`

### Production (Docker):
```bash
docker-compose up -d
```

**API calls:** Frontend calls `/api/*` (relative URL), Nginx proxies to backend

## Environment Variables

Environment variables are defined in `docker-compose.yml`:

```yaml
backend:
  environment:
    DB_USER: postgres
    DB_HOST: postgres        # ← Container hostname, not localhost
    DB_NAME: kindalike
    DB_PASSWORD: kindalike123
    DB_PORT: 5432
    PORT: 5000
    JWT_SECRET: kindalike_secret_key_2024
```

**For production:** Use `.env` file or Docker secrets for sensitive data.

## Data Persistence

Your database data is stored in a Docker volume:

```bash
# List volumes
docker volume ls

# Inspect volume
docker volume inspect kindalike_postgres_data

# Backup database
docker exec kindalike_db pg_dump -U postgres kindalike > backup.sql

# Restore database
docker exec -i kindalike_db psql -U postgres kindalike < backup.sql
```

## Updating the Application

### Update Frontend Code:
1. Make changes to React code
2. Rebuild: `docker-compose up -d --build frontend`

### Update Backend Code:
1. Make changes to Python code
2. Rebuild: `docker-compose up -d --build backend`

### Update Database Schema:
1. Edit `database/init.sql`
2. Remove old data: `docker-compose down -v`
3. Start fresh: `docker-compose up -d`

**⚠️ Note:** Changing `init.sql` only affects new databases. For existing databases, use migrations.

## Troubleshooting

### Containers won't start:
```bash
# Check logs
docker-compose logs

# Check if ports are in use
netstat -ano | findstr :80
netstat -ano | findstr :5000
netstat -ano | findstr :5432
```

### Frontend can't reach backend:
```bash
# Check if backend is running
docker-compose ps

# Check backend logs
docker-compose logs backend

# Test backend health
curl http://localhost:5000/health
```

### Database connection errors:
```bash
# Check if postgres is ready
docker-compose ps postgres

# Check postgres logs
docker-compose logs postgres

# Test connection
docker exec kindalike_db psql -U postgres -d kindalike -c "SELECT 1;"
```

### Build failures:
```bash
# Clean rebuild
docker-compose down
docker-compose build --no-cache
docker-compose up -d
```

### Remove everything and start fresh:
```bash
# Stop and remove containers, networks, volumes
docker-compose down -v

# Remove images
docker rmi kindalike-frontend kindalike-backend

# Start fresh
docker-compose up -d --build
```

## Production Deployment

For production deployment (AWS, Google Cloud, etc.):

### 1. Use Environment Variables:
```yaml
backend:
  environment:
    DB_PASSWORD: ${DB_PASSWORD}  # From .env file
    JWT_SECRET: ${JWT_SECRET}    # From .env file
```

### 2. Use Docker Secrets:
```yaml
secrets:
  db_password:
    file: ./secrets/db_password.txt
```

### 3. Add HTTPS:
- Use a reverse proxy (Nginx, Traefik, Caddy)
- Get SSL certificates (Let's Encrypt)

### 4. Scale Services:
```bash
docker-compose up -d --scale backend=3
```

### 5. Use Production Database:
- AWS RDS
- Google Cloud SQL
- Managed PostgreSQL

## Comparison: Docker vs Manual Setup

| Aspect | Docker | Manual |
|--------|--------|--------|
| **Setup** | One command | Multiple steps |
| **Consistency** | Same everywhere | May differ |
| **Dependencies** | Built-in | Manual install |
| **Networking** | Automatic | Manual config |
| **Cleanup** | `docker-compose down` | Uninstall everything |
| **Good for** | Production, CI/CD | Development |

## Next Steps

1. ✅ Run `docker-compose up -d`
2. ✅ Visit http://localhost
3. ✅ Create an account
4. ✅ Fill out the survey
5. ✅ Check the database:
   ```bash
   docker exec -it kindalike_db psql -U postgres -d kindalike -c "SELECT * FROM users;"
   ```

## Questions?

- Check container logs: `docker-compose logs -f`
- Check container status: `docker-compose ps`
- Read the main README.md
- Read SETUP_GUIDE.md for manual setup
