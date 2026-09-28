FROM python:3.11-slim

# Install system dependencies, tesseract-ocr, and language packs (English, Thai & OSD)
RUN apt-get update && apt-get install -y --no-install-recommends \
    tesseract-ocr \
    tesseract-ocr-tha \
    tesseract-ocr-eng \
    tesseract-ocr-osd \
    libgl1 \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# Install Python requirements
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application files
COPY . .

# Create uploads directory
RUN mkdir -p uploads

ENV PYTHONUNBUFFERED=1
ENV PORT=5000

EXPOSE 5000

CMD ["sh", "-c", "gunicorn --bind 0.0.0.0:${PORT:-5000} --workers 1 --threads 4 --timeout 120 app:app"]
