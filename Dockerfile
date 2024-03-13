# Use an official Python runtime as a parent image
FROM python:3.11-slim-buster

# Set the working directory in the container to /app
WORKDIR /app

# Add the current directory contents into the container at /app
ADD . /app

# Install any needed packages specified in pyproject.toml
RUN pip install poetry
RUN poetry config virtualenvs.create false
RUN poetry install --no-dev

# Make the migrate.sh file executable
RUN chmod +x migrate.sh

# Run app.py when the container launches
CMD ./migrate.sh && python app.py
