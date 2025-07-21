FROM python:3.11-slim

WORKDIR /app

# Install dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application
COPY . .

# Create data directory for database
RUN mkdir -p /app/data

# Set environment variable for database location
ENV DATABASE_URL=sqlite:////app/data/youtube_monitor.db

# Run the bot
CMD ["python", "main.py"] 