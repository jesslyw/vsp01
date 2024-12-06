# Dockerfile  docker build -t vs:latest .
FROM python:3.9-slim

# Arbeitsverzeichnis setzen
WORKDIR /app

# Anforderungen kopieren und installieren
COPY requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt

# Flask-App kopieren
COPY . .

# Flask-Umgebung konfigurieren
ENV FLASK_APP=src.app.main.py
ENV FLASK_RUN_HOST=0.0.0.0
ENV FLASK_RUN_PORT=5000

EXPOSE 5000

# Standardbefehl zum Starten der Flask-App
CMD ["flask", "run"]
