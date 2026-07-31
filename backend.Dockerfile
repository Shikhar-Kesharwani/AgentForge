# Use official lightweight Python image
FROM python:3.11-slim

# Prevent Python from writing pyc files to disc
ENV PYTHONDONTWRITEBYTECODE=1
# Prevent Python from buffering stdout and stderr
ENV PYTHONUNBUFFERED=1

WORKDIR /app

# Install dependencies first for Docker caching
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy the rest of the backend codebase
COPY agent/ ./agent/
COPY main.py .

# We don't copy static/ here because in the cloud stack, 
# static is hosted on Vercel. (In local Docker Compose, 
# we can just mount it or serve it separately).

# Default Render port is 10000, but fallback to 8000
ENV PORT=8000
EXPOSE ${PORT}

# Start FastAPI
CMD ["python", "main.py"]
