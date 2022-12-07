## Signaling + Chatting Server 
<img src="https://img.shields.io/badge/python-3776AB?style=flat-square&logo=python&logoColor=white"> <img src="https://img.shields.io/badge/flask-000000?style=flat-square&logo=flask&logoColor=white"> <img src="https://img.shields.io/badge/Redis-F80000?style=flat-square&logo=Redis&logoColor=white"> <img src="https://img.shields.io/badge/Socket.Io-010101?style=flat-square&logo=Socket.IO&logoColor=white"/> <img src="https://img.shields.io/badge/Elasticsearch-7952B3?style=flat-square&logo=Elasticsearch&logoColor=white"/>

- 초기 WebRTC 커넥션 하기 위한 정보인 socketId 를 반환
- 같은방에 있는 유저들끼리  채팅을 하기 위한 socket event 로직 처리
- 채팅에 대한 메타데이터를 ElasticSearch 에 저장하기위한 로직 처리
### socket-Event 명세서 
|event|이름|설명|
|:---:|:---:|:---:|
|create-room|유저 방 생성|유저가 방을 생성하면 client로 부터 이벤트를 수신, 방 정보를Spring API 서버로 전송, 방 생성 메타데이터 elasticsearch 로 저장 |
|join-room|유저 방 입장|유저가 방을 입장할때 유저에 대한 정보를 Client로부터 수신, 이후 유저정보를 SpringAPI 서버로 전송 및 response로 받은 user_list에 대한 로직 처리 및 client로 전송, 유저 입장 메타데이터를 Elasticsearch에 저장 |
|disconnect|유저 퇴장|유저가 방을 나갈때 SpringAPI 에 유저 정보 삭제 요청, 유저 퇴장 메타데이터를 Elasticsearch 로 저장|
|data|connection 데이터 송수신|WebRTC connection 을 맺기위한 peer 데이터 송수신|
|chatting|채팅 송수신|Client로 부터 받은 채팅데이터를 ElasticSearch에 저장 |
