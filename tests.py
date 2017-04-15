from flask_socketio import SocketIOTestClient
from pyfakefs import fake_filesystem_unittest
from app import app, socketio

import json
import os
import uuid

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


