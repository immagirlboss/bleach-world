FROM python:3.11-slim

# Install system dependencies for SWI-Prolog
RUN apt-get update && apt-get install -y \
    swi-prolog \
    libswipl-dev \
    && rm -rf /var/lib/apt/lists/*

# Verify SWI-Prolog installed correctly (build will fail if this fails)
RUN swipl --version

WORKDIR /app

# Install Python requirements
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy source code
COPY . .

# Environment variables
ENV PYTHONUNBUFFERED=1
ENV PORT=5000

EXPOSE 5000

# Run the app
CMD ["python", "app.py"]