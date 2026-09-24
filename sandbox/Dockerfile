FROM python:3.9-slim

RUN apt-get update \
    && apt-get install -y --no-install-recommends patch \
    && rm -rf /var/lib/apt/lists/* \
    && pip install --no-cache-dir pytest

WORKDIR /workspace
