FROM ubuntu:22.04

# Avoid prompts during package installation
ENV DEBIAN_FRONTEND=noninteractive

# Install Python, Pip, and SWI-Prolog (available in default Ubuntu repos)
RUN apt-get update && apt-get install -y \
    python3 \
    python3-pip \
    swi-prolog \
    && rm -rf /var/lib/apt/lists/*

# Verify SWI-Prolog installed correctly
RUN swipl --version

WORKDIR /app

# Install Python requirements
COPY requirements.txt .
RUN pip3 install --no-cache-dir -r requirements.txt

# Copy source code
COPY . .

# Environment variables
ENV PYTHONUNBUFFERED=1
ENV PORT=8000

EXPOSE 8000

# Run the app
CMD ["python3", "app.py"]