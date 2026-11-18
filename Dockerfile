FROM python:3.13-slim

WORKDIR /app

ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

RUN pip install --no-cache-dir --upgrade pip
COPY requirements.txt requirements-dev.txt /app
RUN pip install --no-cache-dir -r requirements.txt -r requirements-dev.txt

COPY . /app

RUN useradd --uid 1000 --create-home app
USER app
