# Use an official Python runtime as a parent image
FROM python:3.12-slim

# Set environment variables
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

# Set the working directory in the container
WORKDIR /app

# Copy requirements first to leverage Docker cache
COPY requirements.txt /app/

# Install dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Copy the rest of the application code
COPY . /app/

# Create a volume for the SQLite database so it persists across container restarts
VOLUME ["/app/data"]

# Expose the port that the Flask admin panel uses (Back4App will map this dynamically via the PORT env var)
EXPOSE 5000

# Run main.py when the container launches
CMD ["python", "main.py"]
