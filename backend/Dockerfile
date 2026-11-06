# Build from the PROJECT ROOT, not from backend/:
#   docker build -f backend/Dockerfile -t cyberlife-api .
FROM python:3.12-slim
ENV PYTHONDONTWRITEBYTECODE=1 PYTHONUNBUFFERED=1
WORKDIR /app
COPY backend/requirements.txt ./requirements.txt
RUN pip install --no-cache-dir -r requirements.txt
COPY backend/app ./app
COPY content /content
ENV CYBERLIFE_CONTENT_DIR=/content CYBERLIFE_SERVE_FRONTEND=false CYBERLIFE_ENV=production
EXPOSE 8000
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
