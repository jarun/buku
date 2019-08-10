FROM python:alpine

MAINTAINER Ameya Shenoy "shenoy.ameya@gmail.com"


COPY . /Buku
RUN set -ex \
  && apk add --no-cache \
    git \
    gcc \
    openssl-dev \
    musl-dev \
    libffi-dev \
  && pip install -U --no-cache-dir \
    pip \
  && cd Buku \
  && pip install --no-cache-dir .[server]

ENTRYPOINT FLASK_ENV=production FLASK_APP=/Buku/bukuserver/server.py flask run --host 0.0.0.0 --port 5001
EXPOSE 5001

