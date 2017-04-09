from flask_socketio import SocketIOTestClient
from app import app, socketio

import pyfakefs.fake_filesystem as fake_fs
import unittest

class Tests(unittest.TestCase):

    def setUp(self):
        """ Sets up test fixture. """
        app.config['TESTING'] = True
        self.fakefs = fake_fs.FakeFilesystem()
        self.http_client = app.test_client()
        self.ws_client = socketio.test_client(app)

    def tearDown(self):
        """ Tears down test fixture. """
        self.http_client = None
        self.ws_client = None
        app.config['TESTING'] = False

    def test_create_file(self):
        """
        Assert that hitting the /create endpoint
        will create a file with the given value of
        the 'file_contents' key in the json object.
        Assert that we return the created file name to
        the client.
        """
        resp = self.http_client.post('/create',
                                     data={"file_contents": "Hello\nWorld\n!!!"})
        assert False
