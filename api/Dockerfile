FROM python:3.15-slim

WORKDIR /app

ENV PYTHONUNBUFFERED=1
ENV PYTHONDONTWRITEBYTECODE=1

COPY requirements.txt .

RUN pip install --no-cache-dir -r requirements.txt

COPY . .

EXPOSE 17000

CMD ["uvicorn", "app:app", "--host", "0.0.0.0", "--port", "17000", "--workers", "2"]