# Run
FROM python:3.12-alpine
WORKDIR /usr/app

LABEL org.opencontainers.image.source https://github.com/kms0219kms/waklife_manager

COPY ./pyproject.toml .
COPY ./poetry.lock .

RUN apk --no-cache add tzdata && ln -snf /usr/share/zoneinfo/Asia/Seoul /etc/localtime
RUN python3 -m pip install -U pip setuptools
RUN python3 -m pip install poetry

RUN python3 -m poetry install --no-root

COPY . .

CMD ["python3", "bot.py"]
