FROM python:alpine

MAINTAINER Ameya Shenoy "shenoy.ameya@gmail.com"

ENV BUKUSERVER_PORT=5001

COPY . /Buku

RUN set -ex \
  && apk add --no-cache --virtual .build-deps \
    gcc \
    openssl-dev \
    musl-dev \
    libffi-dev \
  && pip install -U --no-cache-dir \
    pip \
    gunicorn \
    /Buku[server] \
  && apk del .build-deps \
  && rm -rf /Buku

HEALTHCHECK --interval=1m --timeout=10s \
  CMD nc -z localhost ${BUKUSERVER_PORT} || exit 1

ENTRYPOINT gunicorn --bind 0.0.0.0:${BUKUSERVER_PORT} "bukuserver.server:create_app()"
EXPOSE ${BUKUSERVER_PORT}

