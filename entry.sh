#!/bin/bash

# This script sets up the development environment for the Anchor-Insight-AI project.
# It installs all the necessary dependencies using pipenv.

echo "Starting Anchor-Insight-AI setup..."

# Check if pip is installed
if ! command -v pip &> /dev/null
then
    echo "pip could not be found. Please install Python and pip first."
    exit 1
fi

# Install pipenv if it's not already installed
if ! command -v pipenv &> /dev/null
then
    echo "pipenv not found. Installing pipenv..."
    pip install pipenv
fi

echo "Installing project dependencies from Pipfile. This may take a few minutes..."

# Use Pipfile to install dependencies
pipenv install --deploy --system

echo "----------------------------------------"
echo "Setup complete!"
echo "All dependencies have been installed."
echo ""
echo "To run the application, use the following command:"
echo "uvicorn src.app.main:app --host 0.0.0.0 --port 8000"
echo "----------------------------------------"