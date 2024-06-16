# Use an official Python runtime as a parent image
FROM python:3.10-slim

# Set the working directory in the container
WORKDIR /app

# Copy the requirements file into the container
COPY requirements.txt .

# Install any needed packages specified in requirements.txt
RUN pip install --no-cache-dir -r requirements.txt

# Copy the rest of the application code into the container
COPY . .

# Set the working directory to src
WORKDIR /app/src

# Make port 4242 available to the world outside this container
EXPOSE 4242

CMD [ "python", "-m", "src.app"]