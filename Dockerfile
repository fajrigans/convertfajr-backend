# Gunakan image Python slim
FROM python:3.11-slim

# Install alat-alat konversi yang dibutuhkan
RUN apt-get update && apt-get install -y \
    ffmpeg \
    pandoc \
    zip \
    tar \
    && rm -rf /var/lib/apt/lists/*

# Set working directory
WORKDIR /app

# Copy semua file ke container
COPY . .

# Install dependency Python
RUN pip install --no-cache-dir -r requirements.txt

# Tentukan port (Railway pakai variabel PORT)
EXPOSE 8080

# Jalankan aplikasi
CMD ["gunicorn", "-w", "2", "-b", "0.0.0.0:8080", "app:app"]


