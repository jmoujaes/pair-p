from flask import Flask, render_template, redirect, request, \
                    jsonify, abort
from flask_socketio import SocketIO, join_room, leave_room
from werkzeug.utils import secure_filename

import diff_match_patch
import json
import logging
import uuid
import werkzeug


UPLOAD_FOLDER = 'user_files/'

# set up logging
fh = logging.FileHandler("webapp.log")
fh.setFormatter(logging.Formatter(
    "%(asctime)s %(filename)s:%(lineno)d %(levelname)s: %(message)s"))
fh.setLevel(logging.DEBUG)

# create and config instance of the app
app = Flask(__name__)
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024 # 16MB
app.logger.addHandler(fh)

socketio = SocketIO(app)
dmp = diff_match_patch.diff_match_patch()


@app.errorhandler(werkzeug.exceptions.NotFound)
def not_found(response):
    """ Show 404 page when a resource is not found. """
    return render_template("not-found.html")

@app.errorhandler(werkzeug.exceptions.InternalServerError)
def error(response):
    """ Show 500 page when an error occurs. """
    return render_template("error.html")

@app.route('/')
def index():
    """ Show a welcome page. """
    return render_template("index.html")

@app.route('/create', methods=['POST'])
def create():
    """
    Creates a file uploaded by the user.
    Expects a POST with a file and filename.
    Optionally, can accept a uuid of an
    existing file that the user has previously
    created.
    """
    # if the client sends a uuid of an existing file
    # return a 200 with the uuid
    if 'file_uuid' in request.data:
        file_uuid = secure_filename(request.data['file_uuid'])
        if os.path.exists(os.path.join(app.config['UPLOAD_FOLDER'],
                                       file_uuid)):
            return jsonify({'file_uuid': file_uuid})

    # if the client does not send a uuid that exists
    # look for file data in the request
    if 'file_contents' not in request.data:
        abort(400, "need file contents")

    filename = uuid.uuid4()
    with open(os.path.join(app.config['UPLOAD_FOLDER'], filename),
              'w') as fdesc:
        fdesc.write(request.data.file_contents)
    return jsonify({"file_uuid": filename})

@socketio.on("join")
def on_join(data):
    """
    When a client sends a 'join' event to the websocket,
    send the client the file with the file_uuid they
    sent, and then add them to the room.
    """
    room = data['file_uuid']
    app.logger.info("Sending file to client as a blob of text.")
    # read file contents and send them to client
    with open(os.path.join(app.config['UPLOAD_FOLDER'],
                           room), 'r') as fdesc:
        file_contents = fdesc.read()
    socketio.emit("file_received",
                  {"file_contents": file_contents},
                  room=request.sid)

    # add the client to the room
    app.logger.info("Adding the client to the room.")
    join_room(room)
    send("New player.", room=room)



@socketio.on("leave")
def on_leave(data):
    """
    When a client requests to leave, we remove them from
    the room.
    """
    room = data['file_uuid']
    leave_room(room)
    send("A player left the room.", room=room)


@socketio.on("diff")
def patch_file(json):
    """
    Patch the specified file with the given diffs.
    If successful, broadcast the diffs to the room.
    Expects a json object with keys 'file_uuid' and
    'diffs' which is an array of diffs.
    """
    app.logger.debug("Received object: %s" % json)
    room = json['file_uuid']
    diffs = json['diffs']

    # make patches from the given diffs
    patches = dmp.patch_make(diffs)

    # read the file contents in
    with open(os.path.join(app.config['UPLOAD_FOLDER'],
                           room), 'r') as fdesc:
        file_contents = fdesc.read()

    # patch the text
    patched_text = dmp.patch_apply(patches, file_contents)

    with open(os.path.join(app.config['UPLOAD_FOLDER'],
                           room), 'w') as fdesc:
        fdesc.write(patched_text)

    # broadcast the diff to everyone in the room
    socketio.emit('diff', diffs, room=room, skip_sid=request.sid)


if __name__ == '__main__':
    socketio.run(app)
