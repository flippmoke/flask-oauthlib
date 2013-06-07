# coding: utf-8

import os
import tempfile
from urlparse import urlparse 
from flask import Flask
from .oauth2_server import create_server
from .oauth2_client import create_client


class BaseSuite(object):
    def setUp(self):
        app = Flask(__name__)
        app.debug = True
        app.testing = True
        app.secret_key = 'development'

        self.db_fd, self.db_file = tempfile.mkstemp()
        config = {
            'SQLALCHEMY_DATABASE_URI': 'sqlite:///%s' % self.db_file
        }

        app = create_server(app)
        app = create_client(app)

        self.app = app
        self.client = app.test_client()
        return app

    def tearDown(self):
        os.close(self.db_fd)
        os.unlink(self.db_file)


authorize_url = (
    '/oauth/authorize?response_type=code&client_id=dev'
    '&redirect_uri=http%3A%2F%2Flocalhost%3A8000%2Fauthorized&scope=email'
)


class TestAuth(BaseSuite):
    def test_login(self):
        rv = self.client.get('/login')
        assert 'response_type=code' in rv.location

    def test_oauth_authorize_invalid_url(self):
        rv = self.client.get('/oauth/authorize')
        assert 'invalid_client_id' in rv.location

        #rv = self.client.get('/oauth/authorize?client_id=dev')
        #print rv.data

    def test_oauth_authorize_valid_url(self):
        rv = self.client.get(authorize_url)
        # valid
        assert '</form>' in rv.data

        rv = self.client.post(authorize_url, data=dict(
            confirm='no'
        ))
        assert 'access_denied' in rv.location

        rv = self.client.post(authorize_url, data=dict(
            confirm='yes'
        ))
        # success
        assert 'code=' in rv.location

    def test_get_access_token(self):
        rv = self.client.post(authorize_url, data={'confirm': 'yes'})
        rv = self.client.get(clean_url(rv.location))
        assert 'access_token' in rv.data

    def test_full_flow(self):
        self.test_get_access_token()
        rv = self.client.get('/')
        assert 'username' in rv.data


def clean_url(location):
    ret = urlparse(location)
    return '%s?%s' % (ret.path, ret.query)
