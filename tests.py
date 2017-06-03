from flask_socketio import SocketIOTestClient
from pyfakefs import fake_filesystem_unittest
from app import app, socketio

import json
import os
import uuid

from unittest import mock

class Tests(fake_filesystem_unittest.TestCase):

    def setUp(self):
        """ Sets up test fixture. """
        app.config['TESTING'] = True
        self.setUpPyfakefs()
        self.http_client = app.test_client()
        self.ws_client = socketio.test_client(app)

        os.mkdir(app.config['UPLOAD_FOLDER'])

    def tearDown(self):
        """ Tears down test fixture. """
        self.http_client = None
        self.ws_client = None
        app.config['TESTING'] = False


    def test_create_file(self):
        """
        Assert that we return the created file name to
        the client.
        Assert that hitting the /create endpoint
        will create a file with the given value of
        the 'file_contents' key in the json object.
        """
        reqdata = {"file_contents": "Hello\nWorld\n!!!"}
        resp = self.http_client.post('/create',
                                     data=json.dumps(reqdata),
                                     content_type="application/json")
        respdata = json.loads(resp.get_data().decode("utf-8"))

        # assert that the view returns json with 'file_uuid' to client
        self.assertIn("file_uuid", respdata)
        self.assertTrue(isinstance(uuid.UUID(respdata["file_uuid"]), uuid.UUID))

        # assert that a file is created on the server
        # with the uuid and file contents
        with open(os.path.join(app.config["UPLOAD_FOLDER"],
                               respdata["file_uuid"]),
                  "r") as fdesc:
            file_contents = fdesc.read()

            self.assertEqual(file_contents, reqdata["file_contents"])

    def test_create_no_filecontents(self):
        """
        Assert that we return a 400 BAD REQUEST when
        file_contents are not included with the POST
        to /create
        """
        reqdata = {}
        resp = self.http_client.post('/create',
                                     data=json.dumps(reqdata),
                                     content_type="application/json")

        self.assertEqual(resp.status_code, 400)

    def test_on_join_event(self):
        """
        Assert that the server receives a "file_uuid"
        when a client joins.
        Assert that the server emits a "file_received"
        event with the contents of the file with the
        name "file_uuid".
        Assert that the server adds the client to the
        room with the value of "file_uuid".
        """
        # create file that the client is requesting
        fileuuid = "1a2b3c4d5e6f7890"
        filedata = "Hello\nWorld\n!!!"
        with open(os.path.join(app.config["UPLOAD_FOLDER"],
                               fileuuid),
                  "w") as fdesc:
            fdesc.write(filedata)

        # client sends the uuid of the
        # file it wants to read/room it wants to join
        # they're the same thing
        self.ws_client.emit("join", {"file_uuid":fileuuid})

        # messages/events the client receives from the server
        received = self.ws_client.get_received()
        self.assertEqual(len(received), 2)

        first = received[0]
        first_name = first['name']
        first_args = first['args']
        self.assertEqual(first_name, "file_received")
        self.assertEqual(first_args[0]['file_contents'], filedata)
        self.assertEqual(first_args[0]['file_uuid'], fileuuid)

        second = received[1]
        second_name = second['name']
        second_args = second['args']
        self.assertEqual(second_name, "message")
        self.assertEqual(second_args, "New player.")

    @mock.patch("app.leave_room")
    def test_on_leave_event(self, mock_leave):
        """
        Assert that the server receives a 'file_uuid'
        when the client emits a leave event.
        Assert that the server removes the client from
        the room.
        Assert that the server tells the room that
        a player left.
        """
        # create file that the client is requesting
        fileuuid = "1a2b3c4d5e6f7890"
        filedata = "Hello\nWorld\n!!!"
        with open(os.path.join(app.config["UPLOAD_FOLDER"],
                               fileuuid),
                  "w") as fdesc:
            fdesc.write(filedata)

        # two clients join the room
        client2 = socketio.test_client(app)
        self.ws_client.emit("join", {"file_uuid":fileuuid})
        client2.emit("join", {"file_uuid":fileuuid})

        # client1 sends the uuid of the
        # room it wants to leave
        self.ws_client.emit("leave", {"file_uuid": "1a2b3c4d5e6f7890"})

        # assert that client is removed from room
        self.assertTrue(mock_leave.called)

        # messages/events the client receives from the server
        received = client2.get_received()
        self.assertEqual(len(received), 3)
        message_after_leave = received[2]
        name = message_after_leave['name']
        args = message_after_leave['args']
        self.assertEqual(name, "message")
        self.assertEqual(args, "A player left the room.")

