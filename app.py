from flask import Flask, render_template, redirect, request, \
                    jsonify, abort
from flask_socketio import SocketIO
from werkzeug.utils import secure_filename

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
    render_template("index.html")

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
    if 'file' not in request.files:
        abort(400, "need file")
    uploaded_file = request.files['file']
    if uploaded_file.filename == "":
        abort(400, "need filename")

    filename = uuid.uuid4()
    uploaded_file.save(os.path.join(app.config['UPLOAD_FOLDER'],
                                    filename))
    return jsonify({"file_uuid": filename})

@socketio.on("connect")
def send_file():
    """
    When a client connects to the websocket, send the
    file to it as a stream of text.
    """
    app.logger.info("Sending file to client as a stream.")
    return


@socketio.on("diff")
def patch_file(json):
    """
    Patch the specified file with the given diff.
    Broadcast the diff to all connected clients.
    """
    app.logger.info("Received object: %s" % json)
    # TODO patch the file
    # TODO broadcast the diff or patch
    return


if __name__ == '__main__':
    socketio.run(app)
