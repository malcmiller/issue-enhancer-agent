FROM python:3.11.10-slim-bookworm

# Use a working directory that won't be overwritten by GitHub Actions
WORKDIR /app

# Install dependencies
COPY requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt

# Copy src folder
COPY src/ ./src/

# ✅ Debug: Confirm script and dependencies are present
RUN echo "Listing contents of /app for verification:" && ls -l /app
RUN echo "Listing /app/src for verification:" && ls -l /app/src

# Entrypoint for GitHub Action
ENTRYPOINT ["python", "/app/src/main.py"]
