FROM python:3.8.15-slim

LABEL maintainer="rhj0830@gmail.com"
# 파일 옮기기 
COPY . /app/server

WORKDIR /app/server
# 환경변수 세팅 및 python module 설치
RUN pip3 install -r requirements.txt

ENTRYPOINT ["python", "Server.py"]
