from flask import Flask, render_template, request, session
from flask_socketio import SocketIO, emit, join_room, send
from flask_cors import CORS

app = Flask(__name__)
CORS(app)
app.config['SECRET_KEY'] = "test key"
socketio = SocketIO(app, cors_allowed_origins="*")

users_in_room = {}
rooms_sid = {}
names_sid = {}

@app.route('/')
def hello():
    return 'hello'

def messageReceived():
    print('message was received!!!')

# @socketio.on('connect') ################### test
# def test_connect():
#     print("goooooooooooooooooooooooooooooooood")
#     emit('pong')
    
@socketio.on('ping')
def test_ping():
    print('ponggggggggg')


@app.route("/join", methods=["GET"])
def join():
    display_name = request.args.get('display_name')
    mute_audio = request.args.get('mute_audio') # 1 or 0
    mute_video = request.args.get('mute_video') # 1 or 0
    room_id = request.args.get('room_id')
    session[room_id] = {"name": display_name,
                        "mute_audio": mute_audio, "mute_video": mute_video}
    return render_template("join.html", room_id=room_id, display_name=session[room_id]["name"], mute_audio=session[room_id]["mute_audio"], mute_video=session[room_id]["mute_video"])

@socketio.on("create-room")
def on_create_room(data):
    session[data["room_id"]] = {
        "name": data["display_name"],
        "mute_audio": data["mute_audio"],
        "mute_video": data["mute_video"]
    }
    print(session)
    emit("join-request")

@socketio.on("connect")
def on_connect():
    sid = request.sid
    print("New socket connected ", sid)


@socketio.on("join-room")
def on_join_room(data):
    sid = request.sid
    room_id = data["room_id"]
    display_name = session[room_id]["name"]
    print(sid)
    
    # register sid to the room
    join_room(room_id)
    rooms_sid[sid] = room_id
    names_sid[sid] = display_name
    
    # broadcast to others in the room
    print("[{}] New member joined: {}<{}>".format(room_id, display_name, sid))
    emit("user-connect", {"sid": sid, "name": display_name},
        broadcast=True, include_self=False, room=room_id)
    # broadcasting시 동일한 네임스페이스에 연결된 모든 클라이언트에게 메시지를 송신함
    # include_self=False 이므로 본인을 제외하고 broadcasting
    # room=room_id인 room에 메시지를 송신합니다. broadcast의 값이 True이어야 합니다.
    print("user-connect active")
    # add to user list maintained on server
    if room_id not in users_in_room:
        users_in_room[room_id] = [sid]
        emit("user-list", {"my_id": sid})  # send own id only
    else:
        usrlist = {u_id: names_sid[u_id]
                   for u_id in users_in_room[room_id]}
        # send list of existing users to the new member
        print(usrlist)
        emit("user-list", {"list": usrlist, "my_id": sid})
        # add new member to user list maintained on server
        users_in_room[room_id].append(sid)

    print("\n users: ", users_in_room, "\n")


@socketio.on("disconnect")
def on_disconnect():
    sid = request.sid
    room_id = rooms_sid[sid]
    display_name = names_sid[sid]

    print("[{}] Member left: {}<{}>".format(room_id, display_name, sid))
    emit("user-disconnect", {"sid": sid},
         broadcast=True, include_self=False, room=room_id)

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
def message(message):
    #sid = request.sid
    #room_id = message["room_id"]
    #display_name = session[room_id]["name"]

    # register sid to the room
    #rooms_sid[sid] = room_id
    #names_sid[sid] = display_name
    print(message)
    
    # broadcast to others in the room
    emit("chatting", message , broadcast=True, include_self=False)

if any(platform.win32_ver()):
    socketio.run(app, debug=True)