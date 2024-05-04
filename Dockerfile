# Run
FROM python:3.12-slim
LABEL org.opencontainers.image.source https://github.com/wakzoo-life/manager_bot

WORKDIR /usr/app
RUN apt update && apt install curl tar xz-utils git -y
RUN ln -snf /usr/share/zoneinfo/Asia/Seoul /etc/localtime

COPY requirements.txt .
RUN python3 -m pip install -r /usr/app/requirements.txt

COPY . .

CMD ["python3", "src/bot.py"]
