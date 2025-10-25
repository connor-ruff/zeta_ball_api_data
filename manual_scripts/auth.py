import requests
import urllib.parse
from urllib.parse import urlparse, parse_qs

CLIENT_ID = '<CLIENT_ID>'
CLIENT_SECRET = '<CLIENT_SECRET>'
REDIRECT_URI = 'https://github.com/connor-ruff'
SCOPE = "fspt-r"  # fantasy sports read access
AUTH_CODE = '<AUTH_CODE>'
REFRESH_TOKEN = '<REFRESH_TOKEN>'



def get_first_access_token_link():
    

    params = {
        "client_id": CLIENT_ID,
        "redirect_uri": REDIRECT_URI,
        "response_type": "code",
        "language": "en-us",
        "scope": SCOPE,
    }

    auth_url = "https://api.login.yahoo.com/oauth2/request_auth?" + urllib.parse.urlencode(params)

    print("Visit this URL to authorize:")
    print(auth_url)


def get_access_and_refresh_tokens(auth_code):
    token_url = "https://api.login.yahoo.com/oauth2/get_token"

    data = {
        "grant_type": "authorization_code",
        "redirect_uri": REDIRECT_URI,
        "code": auth_code
    }

    # Yahoo requires HTTP Basic Auth for client credentials
    resp = requests.post(token_url, data=data, auth=(CLIENT_ID, CLIENT_SECRET))
    resp.raise_for_status()
    token_data = resp.json()

    print("Access token:", token_data["access_token"])
    print("Refresh token:", token_data["refresh_token"])

def get_access_token_from_refresh_token(refresh_token, client_id=CLIENT_ID, client_secret=CLIENT_SECRET):

    token_url = "https://api.login.yahoo.com/oauth2/get_token"

    data = {
        "grant_type": "refresh_token",
        "refresh_token": refresh_token
    }

    # Yahoo requires HTTP Basic Auth for client credentials
    resp = requests.post(token_url, data=data, auth=(client_id, client_secret))
    resp.raise_for_status()
    token_data = resp.json()

    print("New access token obtained.")
    return token_data["access_token"]


