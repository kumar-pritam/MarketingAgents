FROM python:3.12-alpine

WORKDIR /app

RUN apk add --no-cache \
    curl \
    gcc \
    g++ \
    libpq-dev \
    postgresql-dev \
    musl-dev

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

ENV PYTHONUNBUFFERED=1
ENV PYTHONDONTWRITEBYTECODE=1

EXPOSE 8000

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]