FROM python:3.8.15-slim

LABEL maintainer="rhj0830@gmail.com"
# 파일 옮기기 
COPY . /app/server

WORKDIR /app/server
# 환경변수 세팅 및 python module 설치
RUN export ES_IP='http://localhost' \
    && export ES_PORT=9200 \
    && export SPRING_IP='http://localhost' \
    && export SPRING_PORT=8080 \
    && export REDIS_IP='redis://localhost' \
    && export REDIS_PORT=6379 \
    && pip3 install -r requirements.txt

ENTRYPOINT ["python", "Server.py"]
