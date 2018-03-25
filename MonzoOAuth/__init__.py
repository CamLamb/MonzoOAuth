from oauth2client.client import OAuth2WebServerFlow, OAuth2Credentials
import string
import random
import httplib2
import json


class MonzoOAuth:

    auth_uri = 'https://auth.monzo.com/'
    token_uri = 'https://api.monzo.com/oauth2/token'
    api_url = 'https://api.monzo.com/'
    http = httplib2.Http()

    def __init__(self, client_id, client_secret, redirect_uri, credentials={}):
        self.client_id = client_id
        self.client_secret = client_secret
        self.redirect_uri = redirect_uri
        self.credentials = credentials
        self.state = None
        self.flow = OAuth2WebServerFlow(
            client_id=self.client_id,
            client_secret=self.client_secret,
            redirect_uri=self.redirect_uri,
            auth_uri=self.auth_uri,
            token_uri=self.token_uri,
            scope='',
            revoke_uri='',
            device_uri='',
            token_info_uri='',
        )

    def get_state(self):
        if not self.state:
            self.state = "".join(random.choice(string.ascii_letters + string.digits) for x in range(24))
        return self.state

    def set_state(self, state):
        self.state = state

    def get_auth_link(self):
        return self.flow.step1_get_authorize_url(state=self.get_state())

    def exchange_code(self, code):
        self.credentials = self.credentials_to_dict(credentials=self.flow.step2_exchange({'code': code}))
        return self.credentials

    def set_credentials(self, credentials):
        self.credentials = credentials

    def authorized(self):
        if self.credentials is not {} and self.credentials is not None:
            return True
        return False

    def query(self, path, options={}):
        if self.authorized():
            auth_creds = OAuth2Credentials(
                access_token=self.credentials['access_token'],
                refresh_token=self.credentials['refresh_token'],
                token_uri=self.credentials['token_uri'],
                client_id=self.credentials['client_id'],
                client_secret=self.credentials['client_secret'],
                scopes=self.credentials['scopes'],
                token_expiry=self.credentials['token_expiry'],
                user_agent=self.credentials['user_agent']
            )
            self.http = auth_creds.authorize(self.http)

            query_string = ''

            if options:
                query_string = '?'
                for key, option in options.items():
                    print(key)
                    print(option)
                    query_string += key + '=' + option + '&'
                query_string = query_string[:-1]

            response = self.http.request(self.api_url + path + query_string)
            return json.loads(response[1])
        return {}

    def credentials_to_dict(self, credentials):
        return {
            'access_token': credentials.access_token,
            'refresh_token': credentials.refresh_token,
            'token_uri': credentials.token_uri,
            'token_expiry': credentials.token_expiry,
            'user_agent': credentials.user_agent,
            'client_id': credentials.client_id,
            'client_secret': credentials.client_secret,
            'scopes': ''
        }
