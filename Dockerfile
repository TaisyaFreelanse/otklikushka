FROM python:3.11-slim

# Install system dependencies for browser automation
RUN apt-get update && apt-get install -y --no-install-recommends \
    wget \
    curl \
    gnupg \
    unzip \
    ca-certificates \
    fonts-liberation \
    libasound2 \
    libatk-bridge2.0-0 \
    libatk1.0-0 \
    libcups2 \
    libdbus-1-3 \
    libdrm2 \
    libgbm1 \
    libglib2.0-0 \
    libnspr4 \
    libnss3 \
    libx11-xcb1 \
    libxcomposite1 \
    libxdamage1 \
    libxfixes3 \
    libxrandr2 \
    xdg-utils \
    xvfb \
    && rm -rf /var/lib/apt/lists/*

# Install Microsoft Edge
RUN curl https://packages.microsoft.com/keys/microsoft.asc | gpg --dearmor > microsoft.gpg \
    && install -o root -g root -m 644 microsoft.gpg /etc/apt/trusted.gpg.d/ \
    && sh -c 'echo "deb [arch=amd64,arm64,armhf signed-by=/etc/apt/trusted.gpg.d/microsoft.gpg] https://packages.microsoft.com/repos/edge stable main" > /etc/apt/sources.list.d/microsoft-edge-dev.list' \
    && rm microsoft.gpg \
    && apt-get update \
    && apt-get install -y microsoft-edge-stable \
    && rm -rf /var/lib/apt/lists/*

# Set working directory
WORKDIR /app

# Copy requirements first for better caching
COPY requirements.txt .

# Install Python dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY . .

# Create directory for cookies and database (will be mounted on Render)
RUN mkdir -p /app/data || true

# Set environment variables for headless mode
ENV HEADLESS_BROWSER=true
ENV BROWSER_TYPE=edge
ENV DISPLAY=:99

# Expose port for health check
EXPOSE 8000

# Run the bot (health check starts automatically)
CMD ["python", "bot.py"]

