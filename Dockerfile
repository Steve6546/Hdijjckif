# Use an official Python runtime as a parent image
FROM python:3.9-slim

# Set the working directory in the container
WORKDIR /app

# Install system dependencies needed for Pillow (JPEG, PNG support)
# Use --no-install-recommends to reduce image size
# Clean up apt cache afterwards
RUN apt-get update && \
    apt-get install -y libjpeg-dev zlib1g-dev --no-install-recommends && \
    rm -rf /var/lib/apt/lists/*

# Copy the requirements file into the container at /app
COPY requirements.txt .

# Install any needed packages specified in requirements.txt
# Use --no-cache-dir to reduce image size
RUN pip install --no-cache-dir -r requirements.txt

# Copy the rest of the application code into the container at /app
COPY . .

# Removed npm install and related config copies as they are not needed for the Python runtime image.
# If frontend build steps are required, consider using a multi-stage Docker build.

# Make port 8000 available to the world outside this container
EXPOSE 8000

# Define environment variables if needed (e.g., for API keys)
# ENV GITHUB_TOKEN=your_token
# ENV GITHUB_REPO=your_repo
# ENV OPENROUTER_API_KEY=your_key

# Run app.py when the container launches
# Corrected to use the filename 'app' and the FastAPI instance 'app'
CMD ["uvicorn", "app:app", "--host", "0.0.0.0", "--port", "8000"]