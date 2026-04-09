# 1. Start with a standard Linux Python environment
FROM python:3.11-slim

# 2. Install the system-level Chrome and ChromeDriver
RUN apt-get update && apt-get install -y \
    chromium \
    chromium-driver \
    && rm -rf /var/lib/apt/lists/*

# 3. Set the root working directory
WORKDIR /app

# 4. Copy all your files into the container
COPY . .

# 5. Install requirements (checks root first, then tasks folder if it misses)
RUN pip install --no-cache-dir -r requirements.txt || pip install --no-cache-dir -r tasks/requirements.txt

# 6. Navigate into the tasks folder securely
WORKDIR /app/tasks

# 7. Start the RQ worker
CMD ["rq", "worker"]