from flask import Flask, render_template, request, session
from flask_socketio import SocketIO, emit, join_room, send

app = Flask(__name__)
app.config['SECRET_KEY'] = "test key"
socketio = SocketIO(app, cors_allowed_origins="*")

users_in_room = {}
rooms_sid = {}
names_sid = {}

@app.route('/')
def hello():
    return 'hello'

@socketio.on('connect') ################### test
def test_connect():
    print("connection is successs")


@app.route("/join", methods=["GET"])
def join():
    return render_template("join.html")

@socketio.on("create-room")
def on_create_room(data):
    session[data["room_id"]] = {
        "name": data["display_name"],
        "mute_audio": data["mute_audio"],
        "mute_video": data["mute_video"]
    }
    print(session)
    emit("join-request")


@socketio.on("join-room")
def on_join_room(data):
    sid = request.sid
    room_id = data["room_id"]
    display_name = session[room_id]["name"]
    
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

# leave_room은 사용하지 않아도 되는지?

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
def send_message(message):
    sender = message["sender"]
    text = message["text"]
    room_id = message["room_id"]
    # broadcast to others in the room
    emit("chatting", message , broadcast=True, include_self=True, room=room_id)

if __name__ == '__main__':
    socketio.run(app,
        host="0.0.0.0",
        port=5000,
        debug=True 
        #ssl_context=("cert.pem", "key.pem")
    )