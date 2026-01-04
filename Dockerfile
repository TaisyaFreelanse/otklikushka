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
    x11-utils \
    x11-xserver-utils \
    && rm -rf /var/lib/apt/lists/*

# Install Google Chrome (better for Linux servers)
RUN wget -q -O - https://dl-ssl.google.com/linux/linux_signing_key.pub | gpg --dearmor -o /usr/share/keyrings/google-chrome-keyring.gpg \
    && echo "deb [arch=amd64 signed-by=/usr/share/keyrings/google-chrome-keyring.gpg] http://dl.google.com/linux/chrome/deb/ stable main" > /etc/apt/sources.list.d/google-chrome.list \
    && apt-get update \
    && apt-get install -y google-chrome-stable \
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

# Set environment variables
ENV HEADLESS_BROWSER=false
ENV BROWSER_TYPE=chrome
ENV DISPLAY=:99

# Expose port for health check
EXPOSE 8000

# Create startup script that runs Xvfb and bot with better error handling and memory optimization
RUN echo '#!/bin/bash\nset -e\n# Clean up old Xvfb processes\nrm -f /tmp/.X99-lock /tmp/.X11-unix/X99 2>/dev/null || true\npkill -f Xvfb 2>/dev/null || true\nsleep 1\n# Start Xvfb with smaller screen to save memory (1280x720 instead of 1920x1080)\nXvfb :99 -screen 0 1280x720x16 -ac +extension GLX +render -noreset &\nXVFB_PID=$!\nsleep 2\n# Verify Xvfb is running\nif ! kill -0 $XVFB_PID 2>/dev/null; then\n    echo "ERROR: Xvfb failed to start"\n    exit 1\nfi\nexport DISPLAY=:99\nsleep 1\n# Verify DISPLAY is accessible (skip xdpyinfo to save memory)\nif [ ! -S /tmp/.X11-unix/X99 ]; then\n    echo "WARNING: X11 socket not found, but continuing..."\nfi\necho "Xvfb started successfully, DISPLAY=$DISPLAY"\n# Start bot\npython bot.py' > /app/start.sh && chmod +x /app/start.sh

# Run with Xvfb for non-headless mode
CMD ["/bin/bash", "/app/start.sh"]

