FROM python:3.12-slim

WORKDIR /app
ENV PYTHONUNBUFFERED=1

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY bovari_bot ./bovari_bot

VOLUME ["/app/data"]
CMD ["python", "-m", "bovari_bot"]
