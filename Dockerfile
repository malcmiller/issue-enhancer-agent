FROM python:3.11.10-slim-bookworm

# Use a working directory that won't be overwritten by GitHub Actions
WORKDIR /app

# Install dependencies
COPY requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt

# Copy main script
COPY enhance_issue.py ./

# ✅ Debug: Confirm script and dependencies are present
RUN echo "Listing contents of /app for verification:" && ls -l /app

# Optional: See what's inside the GitHub Actions mount (will be empty at build time)
RUN echo "Listing /github/workspace contents at build time (usually empty):" && ls -l /github/workspace || true

# Entrypoint for GitHub Action
ENTRYPOINT ["python", "/app/enhance_issue.py"]
