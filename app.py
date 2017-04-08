from flask import Flask, render_template
from flask_socketio import SocketIO

import logging

# create instance of the app
app = Flask(__name__)
socketio = SocketIO(app)

# set up logging
fh = logging.FileHandler("webapp.log")
fh.setFormatter(logging.Formatter(
    "%(asctime)s %(filename)s:%(lineno)d %(levelname)s: %(message)s"))
fh.setLevel(logging.DEBUG)
app.logger.addHandler(fh)



if __name__ == '__main__':
    socketio.run(app)
