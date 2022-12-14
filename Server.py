from flask import Flask, request, session
from flask_socketio import SocketIO, emit, join_room
from elasticsearch import Elasticsearch
from elasticsearch import helpers
import datetime
import redis
import requests
import json
from pydantic import BaseSettings
from flask_session import Session
from Crypto.Cipher import AES
from Crypto.Util.Padding import pad, unpad
import hashlib
import base64


class Settings(BaseSettings):
    ES_IP: str = 'http://localhost'
    ES_PORT: int = 9200
    SPRING_IP: str = 'localhost'
    SPRING_PORT: int = 8080
    REDIS_IP: str = 'redis://localhost'
    REDIS_PORT: int = 6379


ES_IP = Settings().dict()['ES_IP']
ES_PORT = Settings().dict()['ES_PORT']
SPRING_IP = Settings().dict()['SPRING_IP']
SPRING_PORT = Settings().dict()['SPRING_PORT']
REDIS_IP = Settings().dict()['REDIS_IP']
REDIS_PORT = Settings().dict()['REDIS_PORT']

print(ES_IP, " ## ", ES_PORT, " ## ", SPRING_IP, " ## ", SPRING_PORT, " ## ", REDIS_IP, " ## ", REDIS_PORT, " ## ")

app = Flask(__name__)
app.config['SECRET_KEY'] = "test key"
# app.config['SESSION_TYPE'] = 'redis'
# app.config['SESSION_PERMANENT'] = False
# app.config['SESSION_USE_SIGNER'] = True
# app.config['SESSION_REDIS'] = redis.from_url(f'{REDIS_IP}:{REDIS_PORT}')
# server_session = Session(app)
socketio = SocketIO(app, message_queue=f'{REDIS_IP}:{REDIS_PORT}', cors_allowed_origins="*")
key = hashlib.pbkdf2_hmac(hash_name='sha256', password=b'pass123#', salt=b'eyestalk', iterations=100)
users_in_room = {}
rooms_sid = {}
names_sid = {}

### elk, kibana
es = Elasticsearch(f'{ES_IP}:{ES_PORT}')  ## 변경
es.info()


def utc_time():
    return datetime.datetime.utcnow().strftime('%Y-%m-%dT%H:%M:%S.%f')[:-3] + 'Z'


def make_index(es, index_name):
    if es.indices.exists(index=index_name):
        es.indices.delete(index=index_name)
        es.indices.create(index=index_name)


index_name = 'webrtc_room'


@app.route('/')
def hello():
    return 'hello'


@socketio.on('connect')
def test_connect():
    print("connection is successs")


@socketio.on("create-room")
def on_create_room(data):
    session[data["roomName"]] = {
        "name": data["userNickname"]
    }
    print(session)

    # Spring 로직 추가 => 방 생성
    response = create_room_request(data, request.sid)
    print("방 생성됨!!!!!!!!!!!!!!!!!")

    emit("join-request")

    # elasticsearch
    room_info = response.json()
    user_nickname = str(data["userNickname"])

    if room_info["roomEnterUser"] == 0:
        room_id = data["roomName"]
        doc_create = {"des": "create room", "room_id": room_id, "user_nickname": user_nickname,
                      "@timestamp": utc_time()}
        es.index(index=index_name, doc_type="log", body=doc_create)


@socketio.on("join-room")
def on_join_room(data):
    sid = request.sid
    room_id = data["roomName"]
    display_name = session[room_id]["name"]

    # register sid to the room
    join_room(room_id)

    # Spring 로직 추가 => 유저 데이터 추가
    response = enter_user_request(data, sid)
    print("###########################")
    print(response)
    print("!!!!!!!!!!!!!!!!!!!!!!!!!!!")
    print(response.json())

    users_in_room = response.json()
    print(type(users_in_room))
    rooms_sid[sid] = room_id
    names_sid[sid] = display_name
    # broadcast to others in the room
    print("[{}] New member joined: {}<{}>".format(room_id, display_name, sid))

    ### elasticsearch
    if len(users_in_room) > 0:
        user_nickname = str(data["userNickname"])
        doc_join = {"des": "New member joined", "room_id": room_id, "user_nickname": user_nickname, "sid": sid,
                    "@timestamp": utc_time()}
        es.index(index=index_name, doc_type="log", body=doc_join)
        emit("user-connect", {"sid": sid, "name": display_name}, broadcast=True, include_self=False, room=room_id)

    message = {
        "sid": sid,
        "name": display_name,
        'type': "join"
    }
    print(message)
    emit("chatting", message, broadcast=True, include_self=True, room=room_id)
    # broadcasting시 동일한 네임스페이스에 연결된 모든 클라이언트에게 메시지를 송신함
    # include_self=False 이므로 본인을 제외하고 broadcasting
    # room=room_id인 room에 메시지를 송신합니다. broadcast의 값이 True이어야 합니다.
    # add to user list maintained on server
    # if room_id not in users_in_room:
    #     users_in_room[room_id] = [sid]
    #     emit("user-list", {"my_id": sid})  # send own id only
    # else:
    #     usrlist = {u_id: names_sid[u_id]
    #                for u_id in users_in_room[room_id]}
    #     # { socketId : userName ... } 형태의 json
    #     # send list of existing users to the new member
    #     print("usrlist :::::::::::::::::::::::")
    #     print(usrlist)
    #     emit("user-list", {"list": usrlist, "my_id": sid})
    #     # add new member to user list maintained on server
    #     users_in_room[room_id].append(sid)
    #
    print(len(users_in_room))
    if len(users_in_room) == 1:
        print("이거 실행됨")
        emit("user-list", {"my_id": sid})
    else:
        print(users_in_room)
        usrlist = users_in_room
        del usrlist[sid]
        emit("user-list", {"list": usrlist, "my_id": sid})
        # print
        # for key in users_in_room:
        #     print(key)
        #     print(users_in_room[key])
        #     if users_in_room[key] is display_name:
        #         del usrlist[key]
        #

    # print("\n users: ", users_in_room, "\n")


@socketio.on("disconnect")
def on_disconnect():
    sid = request.sid
    room_id = rooms_sid[sid]
    display_name = names_sid[sid]

    ### elk
    # user_nickname = display_name
    now = datetime.datetime.now()
    now = now.strftime('%m/%d/%y %H:%M:%S')
    doc_disconnect = {"des": "user-disconnect", "room_id": room_id, "sid": sid, "@timestamp": utc_time()}
    es.index(index=index_name, doc_type="log", body=doc_disconnect)

    print("[{}] Member left: {}<{}>".format(room_id, display_name, sid))
    message = {
        "sid": sid,
        "name": display_name,
        'type': "disconnect"
    }
    emit("chatting", message, broadcast=True, include_self=True, room=room_id)

    emit("user-disconnect", {"sid": sid}, broadcast=True, include_self=False, room=room_id)

    # Spring 로직 추가
    response = exit_room(sid)
    print(response)

    users_in_room[room_id].remove(sid)
    if len(users_in_room[room_id]) == 0:
        users_in_room.pop(room_id)

    rooms_sid.pop(sid)
    names_sid.pop(sid)

    print("\nusers: ", users_in_room, "\n")


@socketio.on("data")
def on_data(data):
    sender_sid = data['sender_id']
    target_sid = data['target_id']
    if sender_sid != request.sid:
        print("[Not supposed to happen!] request.sid and sender_id don't match!!!")

    if data["type"] != "new-ice-candidate":
        print('{} message from {} to {}'.format(
            data["type"], sender_sid, target_sid))
    socketio.emit('data', data, room=target_sid)


@socketio.on("chatting")
def send_message(message):
    sender = message["sender"]
    text = message["text"]
    room_id = message["room_id"]

    ### elk

    # date = datetime.datetime.now()
    # now = date.strftime('%m/%d/%y %H:%M:%S')
    # doc_chatting= {"des" : "chatting", "room_id" : room_id, "chatting message" : text,"@timestamp": utc_time()}
    # es.index(index=index_name, doc_type="log", body=doc_chatting)
    user_nickname = str(message["sender"])
    date = datetime.datetime.now()
    now = date.strftime('%m/%d/%y %H:%M:%S')
    # 채팅 암호화 추가
    doc_chatting = {"des": "chatting", "room_id": room_id, "user_nickname": user_nickname,
                    "chatting message": encrypt(text),
                    "@timestamp": utc_time()}
    es.index(index=index_name, doc_type="log", body=doc_chatting)

    data = {
        "text": text,
        "room_id": room_id,
        "sender": sender,
        "type": "normal",
        "direct": False,  # react에서 dm인지 아닌지 확인할 수 있는 필드
        "target": "self"
    }

    # front로부터 받은 data에 direct라는 필드가 있고 false 값이라면 브로드캐스팅을 하고
    # true라면 특정인에게만 채팅(emit)을 보냄
    if "direct" in message:
        if message["direct"] == False:
            emit("chatting", data, broadcast=True, include_self=True, room=room_id)
        else:
            data["direct"] = True
            emit("chatting", data, to=request.sid)
            data["target"] = "other"
            emit("chatting", data, to=message["dest"])

    # broadcast to others in the room
    # emit("chatting", data, room=room_id)


@socketio.on("share-start")
def share_start(data):
    sid = request.sid
    room_id = data["roomName"]
    emit("share-start", {"sid": sid}, broadcast=True, include_self=False, room=room_id)


@socketio.on("share-end")
def share_end(data):
    room_id = data["roomName"]
    sid = request.sid
    emit("share-end", {"sid": sid}, broadcast=True, include_self=False, room=room_id)


def getParam(data, socketID):
    params = json.dumps({
        'userNickname': data['userNickname'],
        'roomName': data['roomName'],
        'roomPassword': data['roomPassword'],
        'roomCapacity': data['roomCapacity'],
        'socketId': socketID
    })
    return params


def create_room_request(data, socketId):
    response = requests.post(f'http://{SPRING_IP}:{SPRING_PORT}/room',
                             data=getParam(data, socketId),
                             headers={'Content-Type': 'application/json'},
                             verify=False
                             )
    return response


def enter_user_request(data, socketId):
    print(data)
    response = requests.post(f'http://{SPRING_IP}:{SPRING_PORT}/room/enter',
                             data=getParam(data, socketId),
                             headers={'Content-Type': 'application/json'},
                             verify=False
                             )
    return response


def exit_room(socketID):
    response = requests.post(f'http://{SPRING_IP}:{SPRING_PORT}/room/exit?socketId={socketID}',
                             headers={'Content-Type': 'application/json'},
                             verify=False
                             )
    return response


def encrypt(data):
    encrypt_data = {}

    aes = AES.new(key, AES.MODE_ECB)
    block_size = 16

    data = data.encode('utf8')  # bytes인코딩
    padded_value = pad(data, block_size)  # 블록 사이즈 맞추기(패딩)

    encrypt_data = base64.b64encode(aes.encrypt(padded_value)).decode('utf8')

    return encrypt_data


def decrypt(data):
    aes = AES.new(key, AES.MODE_ECB)

    block_size = 16
    decrypted_value = aes.decrypt(base64.b64decode(data))  # 복호화
    unpadded_value = unpad(decrypted_value, block_size)  # 암호화 할 때 붙였던 pad 떼어내기

    return unpadded_value.decode('utf-8')


if __name__ == '__main__':
    socketio.run(app,
                 host="0.0.0.0",
                 port=5000
                 )
    make_index(es, index_name)
