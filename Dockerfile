ARG PLAYWRIGHT_TAG=v1.44.0-jammy
FROM mcr.microsoft.com/playwright/python:${PLAYWRIGHT_TAG}

WORKDIR /app

RUN apt-get update && apt-get install -y xvfb netcat-openbsd && rm -rf /var/lib/apt/lists/*

COPY requirements.txt .
RUN pip install -r requirements.txt && playwright install chromium

COPY . .

ENV SOCKS_PORT=9050
ENV CONTROL_PORT=9051
ENV API_PORT=5000

CMD ["sh", "-c", "mkdir -p /logs && until nc -z 127.0.0.1 $SOCKS_PORT && nc -z 127.0.0.1 $API_PORT; do echo 'Waiting for Tor...'; sleep 5; done && while true; do python3 -u thor_main.py -T >> /logs/sessions.log 2>&1; sleep 5; done"]
