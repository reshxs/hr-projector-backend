FROM python:3.10.4-alpine

ENV PYTHONBUFFERED 1

RUN apk add libpq-dev
RUN apk add build-base

RUN mkdir -p app
WORKDIR app

COPY src /app
RUN pip install --upgrade pip
RUN pip install --no-cache-dir -r requirements.txt

# Collect static files before change user due to sudo permissions required:
RUN python3 manage.py collectstatic --no-input --clear

RUN adduser -D user
USER user

CMD ["python", "run.py", "web", "--no-uvicorn-debug", "--no-collectstatic", "--migrate"]
