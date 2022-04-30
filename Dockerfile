FROM python:3.9-alpine

ENV PYTHONBUFFERED 1

RUN apk add libpq-dev build-base
COPY src/requirements.txt ./

RUN pip install --upgrade pip && pip install --no-cache-dir -r requirements.txt

RUN mkdir -p app
WORKDIR app

COPY src /app

# Collect static files before change user due to sudo permissions required:
RUN python3 manage.py collectstatic --no-input --clear

RUN adduser -D user
USER user

CMD ["python", "run.py", "web", "--no-uvicorn-debug", "--no-collectstatic"]
