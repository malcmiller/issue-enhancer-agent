FROM python:3.11.10-slim-bookworm

# Match GitHub Actions working directory
WORKDIR /github/workspace

# Copy your script into the same directory
COPY enhance_issue.py /github/workspace/enhance_issue.py

# Install dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Entrypoint
ENTRYPOINT ["python", "enhance_issue.py"]
