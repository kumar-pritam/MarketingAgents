FROM python:3.12-slim-bookworm

WORKDIR /app

RUN apt-get update && \
    apt-get install -y --no-install-recommends \
        curl \
        gcc \
        g++ \
        libpq-dev \
    && rm -rf /var/lib/apt/lists/*

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

RUN rm -rf /root/.cache/pip

COPY . .

RUN rm -rf /app/frontend/.next \
           /app/__pycache__ \
           /app/agent/__pycache__ \
           /app/integrations/__pycache__ \
           /app/utils/__pycache__ \
           /app/data/* \
           2>/dev/null || true

ENV PYTHONUNBUFFERED=1

EXPOSE 8501

HEALTHCHECK CMD curl -f http://localhost:8501/_stcore/health || exit 1

CMD ["streamlit", "run", "app.py", "--server.port=8501", "--server.address=0.0.0.0"]