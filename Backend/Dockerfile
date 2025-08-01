FROM python:3.11-slim

WORKDIR /app

# --- START: New additions for Node.js, npm, npx, and Deno ---
# Update apt package list, install Node.js (which includes npm and npx)
# and then install Deno globally using npm.
# Finally, clean up apt cache to keep the image size down.
RUN apt-get update && \
    apt-get install -y nodejs npm && \
    npm install -g deno && \
    apt-get clean && \
    rm -rf /var/lib/apt/lists/*
# --- END: New additions ---

# Copy requirements.txt
COPY requirements.txt .

# Install Python dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Copy the rest of the application
COPY . .

# Command to run the application
CMD ["python", "main.py"]