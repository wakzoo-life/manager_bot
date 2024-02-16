# Run
FROM python:3.12-alpine
WORKDIR /usr/app

LABEL org.opencontainers.image.source https://github.com/kms0219kms/waklife_manager

COPY ./requirements.txt .

RUN apk --no-cache add tzdata && ln -snf /usr/share/zoneinfo/Asia/Seoul /etc/localtime
RUN python3 -m pip install -U pip setuptools
RUN python3 -m pip install -r /usr/app/requirements.txt

COPY . .

CMD ["python3", "src/bot.py"]
