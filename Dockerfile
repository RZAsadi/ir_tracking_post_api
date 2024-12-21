# Use an official Python runtime as the base image
FROM python:3.11-slim

# Set the working directory in the container
WORKDIR /app

# Install system dependencies including Chrome and required libraries
RUN apt-get update && apt-get install -y \
    wget \
    gnupg \
    chromium \
    chromium-driver \
    && rm -rf /var/lib/apt/lists/*

# Copy the application files to the container
COPY main.py .
COPY tracking.py .
COPY requirements.txt .

# Install the necessary Python dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Add Chrome user
RUN groupadd -r chrome && useradd -r -g chrome -G audio,video chrome \
    && mkdir -p /home/chrome && chown -R chrome:chrome /home/chrome

# Create directory for Chrome data
RUN mkdir -p /data && chown -R chrome:chrome /data

# Set Chrome flags for running in container
ENV CHROME_FLAGS="--headless --no-sandbox --disable-dev-shm-usage --disable-gpu"

# Switch to non-root user
USER chrome

# Expose any necessary ports (optional, for RabbitMQ communication)
EXPOSE 56567

# Set the default command to run the application
CMD ["python", "main.py"]