FROM python:3.11-slim

# Install system dependencies for SWI-Prolog
RUN apt-get update && apt-get install -y \
    swi-prolog \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# Install Python requirements
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy source code
COPY . .

# Environment variables for production
ENV PYTHONUNBUFFERED=1
ENV PORT=5000

EXPOSE 5000

# Run using gunicorn for stability
CMD ["gunicorn", "--bind", "0.0.0.0:5000", "app:app"]