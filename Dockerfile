FROM python:3.11-slim

WORKDIR /app

# Install dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application files
COPY . .

# Create necessary directories
RUN mkdir -p keys messages

# Create a non-root user and switch to it
RUN useradd -m pomchat
RUN chown -R pomchat:pomchat /app
USER pomchat

# Set environment variables
ENV HOST=0.0.0.0
ENV PORT=8000

# Expose the port
EXPOSE 8000

# Run the application
CMD ["python", "server.py"]
