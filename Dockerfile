FROM python:3.10-slim

# -----------------------------
# Python Environment Variables
# -----------------------------
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

# -----------------------------
# Set Working Directory
# -----------------------------
WORKDIR /app

# -----------------------------
# Copy Dependency File First
# (Improves Docker Layer Caching)
# -----------------------------
COPY requirements.txt /app/

# -----------------------------
# Install OS Packages & Python Dependencies
# -----------------------------
RUN apt-get update && apt-get install -y --no-install-recommends \
    curl \
    libgl1 \
    libglib2.0-0 \
    && pip install --no-cache-dir -r requirements.txt \
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/*

# -----------------------------
# Copy Application Source Code
# -----------------------------
COPY . /app/

# -----------------------------
# Application Port
# -----------------------------
EXPOSE 4000

# -----------------------------
# Start Application
# -----------------------------
CMD ["python", "app.py"]
