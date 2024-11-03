# Use ultralytics image as base
FROM ultralytics/ultralytics:latest

# Install nginx and required dependencies
RUN apt-get update && apt-get install -y \
    nginx \
    gcc \
    python3-dev \
    libffi-dev \
    libssl-dev \
    libjpeg-dev \
    zlib1g-dev \
    && rm -rf /var/lib/apt/lists/*

# Create app directory
WORKDIR /app

# Copy requirements first to leverage Docker cache
COPY requirements.txt .
RUN pip3 install -r requirements.txt

# Copy application code and static files
COPY . .

# Copy nginx configuration
COPY nginx.conf /etc/nginx/conf.d/default.conf

# Expose port 80
EXPOSE 80

# Create startup script
RUN echo '#!/bin/bash\nnginx\npython3 /app/server.py' > /start.sh && \
    chmod +x /start.sh

# Start both nginx and the Python application
CMD ["/start.sh"]


