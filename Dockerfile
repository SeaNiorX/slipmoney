FROM python:3.11-slim

# Install system dependencies, tesseract-ocr, and language packs (English & Thai)
RUN apt-get update && apt-get install -y --no-install-recommends \
    tesseract-ocr \
    tesseract-ocr-tha \
    tesseract-ocr-eng \
    libgl1 \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# Install Python requirements
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application files
COPY . .

# Ensure custom traineddata is in system tessdata path if needed
RUN if [ -d "tessdata" ]; then cp tessdata/*.traineddata /usr/share/tesseract-ocr/5/tessdata/ 2>/dev/null || cp tessdata/*.traineddata /usr/share/tesseract-ocr/4.00/tessdata/ 2>/dev/null || true; fi

# Create uploads directory
RUN mkdir -p uploads

ENV PYTHONUNBUFFERED=1
ENV PORT=5000

EXPOSE 5000

CMD ["sh", "-c", "gunicorn --bind 0.0.0.0:${PORT:-5000} --workers 2 --timeout 120 app:app"]
