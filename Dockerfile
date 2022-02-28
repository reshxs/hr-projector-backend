FROM python:3.9.10-slim

ENV PYTHONBUFFERED 1

RUN apt-get -y update && apt-get install -y libpq-dev gcc

RUN mkdir -p app
WORKDIR app

COPY src /app
RUN pip install --upgrade pip
RUN pip install --no-cache-dir -r requirements.txt

EXPOSE 8000

CMD ["python", "run.py", "web", "--no-uvicorn-debug"]