# Django API — production image (gunicorn)
FROM python:3.11-slim

ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PIP_NO_CACHE_DIR=1

WORKDIR /app

# psycopg2-binary ships wheels, so no build toolchain needed.
COPY requirements.txt .
RUN pip install -r requirements.txt

COPY . .

# Collect DRF/admin static assets into STATIC_ROOT (/app/staticfiles).
# DEBUG defaults to True during build, so no DJANGO_SECRET_KEY is required here.
RUN python manage.py collectstatic --noinput

EXPOSE 8000

# 2 workers keeps memory low for the 1 GB free-tier box.
CMD ["gunicorn", "config.wsgi:application", \
     "--bind", "0.0.0.0:8000", \
     "--workers", "2", \
     "--timeout", "60"]
