FROM python:alpine

LABEL org.opencontainers.image.authors="shenoy.ameya@gmail.com"

ENV BUKUSERVER_PORT=5001

COPY . /buku

ARG CRYPTOGRAPHY_DONT_BUILD_RUST=1

RUN set -ex \
  && apk add --no-cache --virtual .build-deps \
    gcc \
    openssl-dev \
    musl-dev \
    libffi-dev \
  && pip install -U --no-cache-dir \
    pip \
    gunicorn \
    /buku[server] \
  && apk del .build-deps \
  && echo "import sys;  bind = '0.0.0.0:${BUKUSERVER_PORT}'" > 'gunicorn.conf.py' \
  && rm -rf /buku

HEALTHCHECK --interval=1m --timeout=10s \
  CMD nc -z 127.0.0.1 ${BUKUSERVER_PORT} || exit 1

ENTRYPOINT ["gunicorn", "bukuserver.server:create_app()"]
EXPOSE ${BUKUSERVER_PORT}
