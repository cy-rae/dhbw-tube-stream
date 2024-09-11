# Use an official Python runtime as a parent image
FROM python:3.12-slim

# Set the working directory
WORKDIR /app

# Copy the requirements.txt in the working directory
COPY requirements.txt .

## Set proxy environment variables for Bosch environment
#ENV http_proxy=http://rb-proxy-de.bosch.com:8080
#ENV https_proxy=http://rb-proxy-de.bosch.com:8080

# Install any needed packages specified in requirements.txt
RUN pip install --no-cache-dir -r requirements.txt

# Copy the rest of the application code into the working directory
COPY . .

# Make port 5001 available to the world outside this container
EXPOSE 5001

# Define environment variable
ENV FLASK_APP=app
ENV FLASK_ENV=production

# Run app.py when the container launches so that the Flask server starts as entry point
CMD ["flask", "run", "--host=0.0.0.0"]
