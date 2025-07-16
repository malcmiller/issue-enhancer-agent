FROM python:3.11.10-slim-bookworm

WORKDIR /app

# Install dependencies
COPY requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt

# Copy source code
COPY enhance_issue.py ./

# Entrypoint for GitHub Action
ENTRYPOINT ["python", "enhance_issue.py"]
