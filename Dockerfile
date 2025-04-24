FROM python:3.11-slim

# Install dependencies
RUN apt-get update && apt-get install -y \
    ffmpeg \
    pandoc \
    texlive-latex-base \
    texlive-fonts-recommended \
    texlive-extra-utils \
    poppler-utils \
    zip \
    tar \
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/*

# Install Python packages
COPY requirements.txt .
RUN pip install -r requirements.txt

# Copy project files
COPY . .

# Port untuk Railway (gunakan PORT env)
ENV PORT=8080

# Start pakai gunicorn
CMD ["gunicorn", "-b", "0.0.0.0:8080", "app:app"]
