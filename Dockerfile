# 1. Start with a clean, standard Linux Python environment
FROM python:3.11-slim

# 2. Install Chromium, ChromeDriver, and all required system libraries
RUN apt-get update && apt-get install -y \
    chromium \
    chromium-driver \
    && rm -rf /var/lib/apt/lists/*

# 3. Set up your app
WORKDIR /app

# 4. Copy requirements and install them
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# 5. Copy the rest of your project (including the tasks folder)
COPY . .

# 6. Run your exact RQ Worker start command
CMD cd tasks && rq worker