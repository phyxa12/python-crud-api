FROM python:3.11-slim

ENV PYTHONUNBUFFERED=1
ENV DATA_FILE=/var/lib/backend_data/messages.json

WORKDIR /app

COPY app.py .

EXPOSE 5000

HEALTHCHECK --interval=10s --timeout=3s --start-period=5s --retries=3 \
  CMD python -c "import sys, urllib.request; sys.exit(0 if urllib.request.urlopen('http://127.0.0.1:5000/health', timeout=2).status == 200 else 1)"

CMD ["python", "app.py"]
