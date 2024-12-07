# Dockerfile  docker build -t vs:latest .
FROM python:3.11-slim

# Arbeitsverzeichnis setzen
WORKDIR /app

# Anforderungen kopieren und installieren
COPY requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt

# Flask-App kopieren
COPY . .

# Flask-Umgebung konfigurieren
#ENV FLASK_APP=src.main.py
#ENV FLASK_RUN_HOST=0.0.0.0
#ENV FLASK_RUN_PORT=5000

EXPOSE 8000-9000
EXPOSE 8000-9000/udp

CMD ["sh", "-c", "cd src && python main.py"]
