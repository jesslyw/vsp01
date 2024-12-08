# Dockerfile  docker build -t vs:latest .
FROM python:3.11-slim

# Arbeitsverzeichnis setzen
WORKDIR /app/src

# Anforderungen kopieren und installieren
COPY requirements.txt /app/
RUN pip install --no-cache-dir -r ../requirements.txt

# App kopieren
COPY src/ /app/src

# Flask-Umgebung konfigurieren
#ENV FLASK_APP=src.main.py
#ENV FLASK_RUN_HOST=0.0.0.0
#ENV FLASK_RUN_PORT=5000

EXPOSE 8000-9000
EXPOSE 8000-9000/udp

ENTRYPOINT ["python", "main.py"]
