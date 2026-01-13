# Use Python 3.10 slim image
FROM python:3.10-slim

# Set working directory
WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    gcc \
    postgresql-client \
    && rm -rf /var/lib/apt/lists/*

# Install Poetry
RUN pip install poetry==2.1.4

# Copy Poetry files
COPY pyproject.toml poetry.lock* ./

# Configure Poetry to not create virtual environment (we're already in a container)
RUN poetry config virtualenvs.create false

# Install dependencies (--only main replaces deprecated --no-dev)
RUN poetry install --no-root --only main --no-interaction --no-ansi

# Copy application code
COPY app ./app

# Expose port
EXPOSE 5000

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
  CMD python -c "import requests; requests.get('http://localhost:5000/health')" || exit 1

# Run the application
CMD ["poetry", "run", "uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "5000"]
