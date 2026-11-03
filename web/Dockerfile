
FROM python:3.15-slim

WORKDIR /app

ENV PYTHONUNBUFFERED=1
ENV PYTHONDONTWRITEBYTECODE=1

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

EXPOSE 16000

CMD ["gunicorn", "--bind", "0.0.0.0:16000", "--workers", "2", "--access-logfile", "/logs/web-access.log", "--error-logfile", "/logs/web-error.log", "app:app"]
