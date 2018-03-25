from oauth2client.client import OAuth2WebServerFlow, OAuth2Credentials
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

    def get_auth_link(self):
        return self.flow.step1_get_authorize_url()

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


class User:
    def __init__(self, monzo: MonzoOAuth):
        self.monzo = monzo

    def get_accounts(self):
        response = self.monzo.query('accounts')

        accounts = []
        for account in response['accounts']:
            accounts.append(Account(monzo=self.monzo, id=account['id'], account=account))

        return accounts


class Account:
    def __init__(self, monzo: MonzoOAuth, id: str, account: dict = None):
        self.monzo = monzo

        if not account:
            accounts = monzo.query('accounts')['accounts']
            for a in accounts:
                if a['id'] == id:
                    account = a
                    break

        self.id = account['id']
        self.description = account['description']
        self.created = account['created']
        self.balance = None
        self.spent_today = None

    def get_balance(self):
        if not self.balance:
            balance = self.monzo.query('balance', {'account_id': self.id})
            self.balance = Price(amount=balance['balance'], currency_code=balance['currency'])
        return self.balance

    def get_spent_today(self):
        if not self.spent_today:
            balance = self.monzo.query('balance', {'account_id': self.id})
            self.spent_today = Price(amount=balance['spend_today'], currency_code=balance['currency'])
        return self.spent_today

    def get_transactions(self):
        response = self.monzo.query('transactions', {'account_id': self.id})

        transactions = []
        for transaction in response['transactions']:
            transactions.append(Transaction(monzo=self.monzo, id=transaction['id'], transaction=transaction))_
        return transactions

    def get_pots(self):
        response = self.monzo.query('pots')

        pots = []
        for pot in response['pots']:
            pots.append(Pot(monzo=self.monzo, id=pot['id'], pot=pot))

        return pots


class Pot:
    def __init__(self, monzo: MonzoOAuth, id: str, pot: dict = None):
        self.monzo = monzo

        if not pot:
            pots = monzo.query('pots')['pots']
            for p in pots:
                if p['id'] == id:
                    pot = p
                    break

        self.id = pot['id']
        self.name = pot['name']
        self.style = pot['style']
        self.balance = pot['balance']
        self.currency = pot['currency']
        self.created = pot['created']
        self.updated = pot['updated']
        self.deleted = pot['deleted']

    def get_name(self):
        return self.name

    def get_balance(self):
        return Price(amount=self.balance, currency_code=self.currency)


class Transaction:

    def __init__(self, monzo: MonzoOAuth, id: str, transaction: dict = None):
        self.monzo = monzo

        if not transaction:
            transaction = monzo.query('transactions/' + id, {'expand[]': 'merchant'})['transaction']

        self.id = transaction['id']
        self.amount = transaction['amount']
        self.currency = transaction['currency']
        self.account_balance = transaction['account_balance']
        self.created = transaction['created']
        self.description = transaction['description']
        self.merchant = transaction['merchant']
        self.notes = transaction['notes']
        self.settled = transaction['settled']

    def get_amount(self):
        return Price(amount=self.amount, currency_code=self.currency)


class Price:
    def __init__(self, amount, currency_code):
        self.amount = amount
        self.currency_code = currency_code
