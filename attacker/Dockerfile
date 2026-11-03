FROM mcr.microsoft.com/playwright/python:v1.64.1-noble

WORKDIR /attacker

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

ENTRYPOINT ["python", "app.py"]
