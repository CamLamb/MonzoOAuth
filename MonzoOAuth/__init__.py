import json
import os

import httplib2
from oauth2client.client import OAuth2WebServerFlow, OAuth2Credentials
from oauth2client.file import Storage


class MonzoOAuth:
    auth_uri = 'https://auth.monzo.com/'
    token_uri = 'https://api.monzo.com/oauth2/token'
    api_url = 'https://api.monzo.com/'
    http = httplib2.Http()

    def __init__(self, client_id, client_secret, redirect_uri, credentials: dict=None, token_file_path=None):
        self.client_id = client_id
        self.client_secret = client_secret
        self.redirect_uri = redirect_uri

        self.credentials = None
        if credentials:
            self.credentials = OAuth2Credentials(
                access_token=credentials['access_token'],
                client_id=credentials['client_id'],
                client_secret=credentials['client_secret'],
                refresh_token=credentials['refresh_token'],
                token_expiry=credentials['token_expiry'],
                token_uri=credentials['token_uri'],
                user_agent=credentials['user_agent'],
                scopes=credentials['scopes']
            )

        self.token_file_path = token_file_path
        if token_file_path and os.path.exists(token_file_path):
            self.credentials = Storage(token_file_path).get()

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
        self.credentials = self.flow.step2_exchange({'code': code})

        if self.token_file_path and os.path.exists(self.token_file_path):
            Storage(self.token_file_path).put(self.credentials)

        return self.credentials_to_dict(self.credentials)

    def authorized(self):
        if self.credentials is not {} and self.credentials is not None:
            return True
        return False

    def query(self, path, options: dict = None):
        if self.authorized():
            self.http = self.credentials.authorize(self.http)

            query_string = ''

            if options:
                query_string = '?'
                for key, option in options.items():
                    query_string += key + '=' + option + '&'
                query_string = query_string[:-1]

            response = self.http.request(self.api_url + path + query_string)
            return json.loads(response[1])
        return {}

    @staticmethod
    def credentials_to_dict(credentials):
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
        self.total_balance = None
        self.accounts = []
        self.get_accounts()
        self.pots = []
        self.get_pots()

    def get_accounts(self):
        if not self.accounts:
            response = self.monzo.query('accounts')

            accounts = []
            for account in response['accounts']:
                accounts.append(Account(monzo=self.monzo, aid=account['id'], account=account))
            self.accounts = accounts

        return self.accounts

    def get_pots(self):
        if not self.pots:
            response = self.monzo.query('pots')

            pots = []
            for pot in response['pots']:
                pots.append(Pot(monzo=self.monzo, pid=pot['id'], pot=pot))

            self.pots = pots

        return self.pots

    def get_total_balance(self):
        if not self.total_balance:
            total_balance = Price(amount=0, currency_code='GBP')

            accounts = self.get_accounts()
            for account in accounts:
                total_balance = total_balance.add(account.get_balance())

            pots = self.get_pots()
            for pot in pots:
                total_balance = total_balance.add(pot.get_balance())
            self.total_balance = total_balance

        return self.total_balance


class Account:
    def __init__(self, monzo: MonzoOAuth, aid: str, account: dict = None):
        self.monzo = monzo

        if not account:
            accounts = monzo.query('accounts')['accounts']
            for a in accounts:
                if a['id'] == aid:
                    account = a
                    break

        self.id = account['id']
        self.description = account['description']
        self.created = account['created']
        self.closed = account['closed']
        self.balance = None
        self.get_balance()
        self.spent_today = None
        self.get_spent_today()
        self.transactions = []
        self.get_transactions()

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
        if not self.transactions:
            response = self.monzo.query('transactions', {'account_id': self.id})

            transactions = []
            for transaction in response['transactions']:
                transactions.append(Transaction(monzo=self.monzo, tid=transaction['id'], transaction=transaction))

            self.transactions = transactions
        return self.transactions


class Pot:
    def __init__(self, monzo: MonzoOAuth, pid: str, pot: dict = None):
        self.monzo = monzo

        if not pot:
            pots = monzo.query('pots')['pots']
            for p in pots:
                if p['id'] == pid:
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

    def __init__(self, monzo: MonzoOAuth, tid: str, transaction: dict = None):
        self.monzo = monzo

        if not transaction:
            transaction = monzo.query('transactions/' + tid, {'expand[]': 'merchant'})['transaction']

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

    def add(self, price: 'Price'):
        if self.currency_code == price.currency_code:
            new_amount = self.amount + price.amount
            return Price(amount=new_amount, currency_code=self.currency_code)
        return None
