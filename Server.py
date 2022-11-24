import json
import requests
import redis
from flask import Flask, render_template, request, session, jsonify
from flask_socketio import SocketIO, emit, join_room, send
# from elasticsearch import Elasticsearch

# from elasticsearch import helpers
import datetime


# 데이터베이스 연결부분 추가

# db = SQLAlchemy()
app = Flask(__name__)
# app.config['SECRET_KEY'] = "test key"
# app.config['SQLALCHEMY_DATABASE_URI'] = db_url
# db.init_app(app)

socketio = SocketIO(app, message_queue="redis://localhost:6379", cors_allowed_origins="*")

#users_in_room = {}
rooms_sid = {}
names_sid = {}


### elk, kibana
# es = Elasticsearch('http://192.168.56.141:9200')  ## 변경
# es.info()
# def checkSession(room_id):
#     sql = f"select r.room_name,u.user_nickname from room r join user u on r.room_idx = u.room_idx" \
#           f" where r.room_name = \'{room_id}\'"
#     result = db.engine.execute(sql)
#
#     room_list = {}
#     for rs in result:
#         if rs['room_name'] in room_list:
#             room_list[rs['room_name']].append({rs['user_nickname']: rs['user_nickname']})
#         else:
#             room_list[rs['room_name']] = [{rs['user_nickname']: rs['user_nickname']}]
#
#     print(room_list)
#     return room_list

def utc_time():
    return datetime.datetime.utcnow().strftime('%Y-%m-%dT%H:%M:%S.%f')[:-3] + 'Z'


def make_index(es, index_name):
    if es.indices.exists(index=index_name):
        es.indices.delete(index=index_name)
        es.indices.create(index=index_name)


index_name = 'webrtc_room'


@socketio.on('connect')  ################### test
def test_connect():
    print("connection is successs")


@socketio.on("create-room")
def on_create_room(data):
    # session[data["room_id"]] = {
    #     "name": data["user_nickname"],
    # }

    room_id = data["roomName"]
    sid = request.sid
    user_nickname = data["userNickname"]
    print(sid)

    print(data)
    response = create_room_request(data, sid)
    print("testtttting")
    # response 상태코드가 정상(로직이 정상적으로 처리되었을 경우)
    if response.status_code == 200:
        join_room(room_id)
        emit("user-connect", {"sid": sid, "name": user_nickname}, broadcast=True, include_self=False, room=room_id)

    # 상태코드 에러 => emit("fail-create-room")
    else:
        # emit("fail-create-room")
        print(response.json()['message'])

    # elk
    # room_id = data["room_id"]
    # date = datetime.datetime.now()
    # now = date.strftime('%m/%d/%y %H:%M:%S')
    # doc_create = {"des": "create room", "room_id": room_id, "@timestamp": utc_time()}
    # es.index(index=index_name, doc_type="log", body=doc_create)


@socketio.on("join-room")
def on_join_room(data):
    sid = request.sid
    room_name = data["roomName"]
    user_nickname = data["userNickname"]

    enter_user_request(data, sid)

    # register sid to the room
    join_room(room_name)
    # rooms_sid[sid] = room_id
    # names_sid[sid] = nickname
    # broadcast to others in the room
    print("[{}] New member joined: {}<{}>".format(room_name, user_nickname, sid))

    ### elk
    # date = datetime.datetime.now()
    # now = date.strftime('%m/%d/%y %H:%M:%S')
    # doc_join = {"des": "New member joined", "room_id": room_id, "sid": sid, "@timestamp": utc_time()}
    # es.index(index=index_name, doc_type="log", body=doc_join)

    emit("user-connect", {"sid": sid, "name": user_nickname}, broadcast=True, include_self=False, room=room_name)
    # broadcasting시 동일한 네임스페이스에 연결된 모든 클라이언트에게 메시지를 송신함
    # include_self=False 이므로 본인을 제외하고 broadcasting
    # room=room_id 인 room에 메시지를 송신합니다. broadcast의 값이 True이어야 합니다.
    # add to user list maintained on server
    users_in_room = read_session_info_user(room_name)
    print(users_in_room)
    #for user in users_in_room:
        #if sid == user['socketId']:
        #    emit("user-list", {"my_id": sid})
        #else:
    emit("user-list", {"list": users_in_room, "my_id": sid}, broadcast=True, include_self=True)
    #if room_name not in users_in_room:
    #    emit("user-list", {"my_id": sid}) # send own id only
    # else:
    #     usrlist = {u_id: names_sid[u_id]
    #                for u_id in users_in_room[room_name]}
    #     # send list of existing users to the new member
    #     print(usrlist)
    #     emit("user-list", {"list": usrlist, "my_id": sid})
    #     # add new member to user list maintained on server
    #     users_in_room[room_id].append(sid)

    print("\n users: ", users_in_room, "\n")


# leave_room은 사용하지 않아도 되는지?

@socketio.on("disconnect")
def on_disconnect():
    sid = request.sid
    exit_room(sid)
    print("#################### after disconnect###########################")


    # display_name = names_sid[sid]

    ### elk
    # now = datetime.datetime.now()
    # now = now.strftime('%m/%d/%y %H:%M:%S')
    # doc_disconnect = {"des": "user-disconnect", "room_id": room_id, "sid": sid, "@timestamp": utc_time()}
    # es.index(index=index_name, doc_type="log", body=doc_disconnect)



    # print("[{}] Member left: <{}>".format(room_id, sid))
    #emit("user-disconnect", {"sid": sid}, broadcast=True, include_self=False, room=room_id)

    # users_in_room[room_id].remove(sid)
    # if len(users_in_room[room_id]) == 0:
    #     users_in_room.pop(room_id)
    #
    # rooms_sid.pop(sid)

    #print("\nusers: ", users_in_room, "\n")


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
    room_id = message["room_id"]
    ### elk
    # date = datetime.datetime.now()
    # now = date.strftime('%m/%d/%y %H:%M:%S')
    # doc_chatting = {"des": "chatting", "room_id": room_id, "chatting message": text, "@timestamp": utc_time()}
    # es.index(index=index_name, doc_type="log", body=doc_chatting)
    # broadcast to others in the room
    emit("chatting", message, broadcast=True, include_self=True, room=room_id)


def getParam(data, socketID):
    params = json.dumps({
        'userNickname': data['userNickname'],
        'roomName': data['roomName'],
        'roomPassword': data['roomPassword'],
        'roomCapacity': data['roomCapacity'],
        'socketId': socketID
    })
    return params


# def get_session_info():
#     # response = requests.get()
#
#     # return response


def create_room_request(data, socketID):
    response = requests.post('http://localhost:8080/room',
                             data=getParam(data, socketID),
                             headers={'Content-Type': 'application/json'},
                             verify=False
                             )
    return response


def enter_user_request(data, socketID):
    print(data)
    response = requests.post(f'http://localhost:8080/room/{data["roomName"]}/enter/{data["roomPassword"]}',
                             data=getParam(data, socketID),
                             headers={'Content-Type': 'application/json'},
                             verify=False
                             )

    print(f'http://localhost:8080/room/{data["roomName"]}/enter/{data["roomPassword"]}')
    return response


def exit_room(socketID):
    response = requests.post(f'http://localhost:8080/room/exit?socketId={socketID}',
                             headers={'Content-Type': 'application/json'},
                             verify=False
                             )
    print("################## response #############  ", response)
    return response


@app.route("/")
def read_session_info_room():
    response = requests.get(f'http://localhost:8080/room/')
    print(response)
    return response.json()


@app.route("/user")
def read_session_info_user(room_name):
    response = requests.get(f'http://localhost:8080/user/{room_name}')
    print(response.json())
    return response.json()


if __name__ == '__main__':
    socketio.run(app,
                 host="0.0.0.0",
                 port=5000,
                 debug=True
                 # ssl_context=("cert.pem", "key.pem")
                 )
    # db.create_all()
    # make_index(es, index_name)
