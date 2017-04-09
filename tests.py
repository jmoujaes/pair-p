from flask_socketio import SocketIOTestClient
from app import app, socketio

import unittest

class Tests(unittest.TestCase):

    def setUp(self):
        """ Sets up test fixture. """
        self.socket_client = socketio.test_client(app)

    def tearDown(self):
        """ Tears down test fixture. """
        self.client = None


#    def test_create_file(
