# Use an official Python runtime as a parent image
FROM python:3.12-slim

# Set environment variables
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1
ENV DATABASE_URL=sqlite+aiosqlite:///./cosf.db
ENV PORT=8000

# Set the working directory in the container
WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Copy the current directory contents into the container at /app
COPY . /app

# Install project dependencies
RUN pip install --no-cache-dir -e .

# Expose the port the app runs on
EXPOSE 8000

# Default command to run the API server
CMD ["cosf", "serve", "--host", "0.0.0.0", "--port", "8000"]
