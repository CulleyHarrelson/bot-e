# Use an official Python runtime as the parent image
FROM python:3.11-slim

# Set environment variables first (optimizes layer caching)
ENV FLASK_APP=api.py
ENV FLASK_RUN_HOST=0.0.0.0
ENV FLASK_RUN_PORT=6464

# Set the working directory in the container to /app
WORKDIR /app

# Install required system packages
RUN apt-get update && apt-get install -y \
    gcc \
    libpq-dev \
&& rm -rf /var/lib/apt/lists/*  # Clean up cache to reduce layer size

# Copy the current directory contents into the container at /app
COPY . /app

# Install any needed packages specified in requirements.txt
RUN pip install --trusted-host pypi.python.org -r requirements.txt

# Make port 6464 available to the world outside this container
EXPOSE 6464

# Run app.py when the container launches
CMD ["flask", "run"]
