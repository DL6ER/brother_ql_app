# Basis-Image mit Python 3.10
FROM python:3.10-slim

# Arbeitsverzeichnis setzen
WORKDIR /app

# Systemabhängigkeiten installieren (für Pillow und Fonts)
RUN apt-get update && apt-get install -y \
    libfreetype6 libjpeg62-turbo zlib1g-dev \
    fonts-dejavu-core && \
    rm -rf /var/lib/apt/lists/*

# Anforderungen kopieren und Python-Abhängigkeiten installieren
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Anwendungscode kopieren
COPY . .

# Sicherstellen, dass settings.json existiert
RUN touch settings.json

# Flask-Anwendung starten
CMD ["python", "app.py"]