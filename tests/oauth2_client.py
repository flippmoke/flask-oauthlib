from flask import Flask, redirect, url_for, session, request, jsonify
from flask_oauthlib.client import OAuth


def create_client(app):
    oauth = OAuth(app)

    dev = oauth.remote_app(
        'dev',
        consumer_key='dev',
        consumer_secret='dev',
        request_token_params={'scope': 'email'},
        base_url='http://127.0.0.1:5000/api/',
        request_token_url=None,
        access_token_method='GET',
        access_token_url='http://127.0.0.1:5000/oauth/access_token',
        authorize_url='http://127.0.0.1:5000/oauth/authorize'
    )

    @app.route('/')
    def index():
        if 'dev_token' in session:
            ret = dev.get('email')
            return jsonify(ret.data)
        return redirect(url_for('login'))

    @app.route('/login')
    def login():
        return dev.authorize(callback=url_for('authorized', _external=True))

    @app.route('/logout')
    def logout():
        session.pop('dev_token', None)
        return redirect(url_for('index'))

    @app.route('/authorized')
    @dev.authorized_handler
    def authorized(resp):
        if resp is None:
            return 'Access denied: error=%s' % (
                request.args['error']
            )
        session['dev_token'] = (resp['access_token'], '')
        return jsonify(resp)

    @app.route('/address')
    def address():
        ret = dev.get('address')
        return ret.raw_data

    @dev.tokengetter
    def get_oauth_token():
        return session.get('dev_token')

    return app


if __name__ == '__main__':
    # DEBUG=1 python oauth2_client.py
    app = Flask(__name__)
    app.debug = True
    app.secret_key = 'development'
    app = create_client(app)
    app.run(host='localhost', port=8000)
