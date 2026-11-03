FROM python:3.15-slim

WORKDIR /app

ENV PYTHONUNBUFFERED=1
ENV PYTHONDONTWRITEBYTECODE=1

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

EXPOSE 18000

CMD ["gunicorn", "--bind", "0.0.0.0:18000", "--workers", "2", "--access-logfile", "-", "--error-logfile", "-", "app:app"]
