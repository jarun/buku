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
    gunicorn \
  && cd Buku \
  && pip install --no-cache-dir .[server]

ENTRYPOINT gunicorn --bind 0.0.0.0:5001 "Buku.bukuserver.server:create_app()"
EXPOSE 5001

