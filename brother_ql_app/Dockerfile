FROM python:3.10-slim

WORKDIR /app

# Systemabhängigkeiten für Pillow und Fonts
RUN apt-get update && apt-get install -y \
    libfreetype6 libjpeg62-turbo zlib1g-dev \
    fonts-dejavu-core && \
    rm -rf /var/lib/apt/lists/*

# Abhängigkeiten installieren
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Anwendung kopieren
COPY . .

# Flask-Anwendung starten
CMD ["python", "app.py"]