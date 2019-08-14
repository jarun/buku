FROM python:alpine

MAINTAINER Ameya Shenoy "shenoy.ameya@gmail.com"

RUN set -ex \
  && apk add --no-cache \
    git \
    gcc \
    openssl-dev \
    musl-dev \
    libffi-dev \
  && pip install -U --no-cache-dir \
    pip \
    gunicorn

COPY . /Buku
RUN cd Buku \
  && pip install --no-cache-dir .[server]

ENTRYPOINT gunicorn --bind 0.0.0.0:5001 --log-level DEBUG "Buku.bukuserver.server:create_app()"
EXPOSE 5001

