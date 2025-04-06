# Use a lightweight Python image
FROM python:3.10-slim

# Set working directory inside the container
WORKDIR /app

# Copy the requirements file from root and install dependencies
COPY requirement.txt .
RUN pip install --no-cache-dir -r requirement.txt

# Copy everything from root to the container
COPY . .

# Set the working directory to backend (where app.py is)
WORKDIR /app/backend

# Expose the required port
EXPOSE 8080

# Run the application
CMD ["gunicorn", "-b", "0.0.0.0:8080", "--timeout", "3600", "app:app"]
