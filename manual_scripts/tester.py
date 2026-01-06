from auth import get_access_token_from_refresh_token
import requests
import xmltodict
import json
import boto3

# FANTASY LEAGUE
LEAGUE_KEY = '466.l.6036'
SEASON_START_WEEK = '2025-10-20'

TEAM_KEYS = [
    '466.l.6036.t.1', # Tommy Dating Nikki
    '466.l.6036.t.15', # Locked In
    '466.l.6036.t.2', # 1 of 1
    '466.l.6036.t.3', # A tinederall story
    '466.l.6036.t.4', #  Don Juan Add
    '466.l.6036.t.10', # Midnight riders
    '466.l.6036.t.5', #  Foe Nem
    '466.l.6036.t.8', # Jer Bears
    '466.l.6036.t.6', #  Hibernation Hoopers
    '466.l.6036.t.9', #  Mexican Mamis
    '466.l.6036.t.7', #  Italian Stallion
    '466.l.6036.t.17', #  Slumpy Boyzzz
    '466.l.6036.t.11', #  Neal Down
    '466.l.6036.t.16' ,#  The Playbook
    '466.l.6036.t.12', #  Net Yurishing
    '466.l.6036.t.14', #  Franklin Fleetwood
    '466.l.6036.t.13',  #  SLOP
    '466.l.6036.t.18'  #  Thots and Prayers
]

# API ENDPOINTS
ACCESS_TOKEN_URL = "https://api.login.yahoo.com/oauth2/get_token"
MATCHUP_WEEK_URL_TEMPLATE = 'https://fantasysports.yahooapis.com/fantasy/v2/league/{league_key}/scoreboard;week={week_number}'
TEAM_ROSTER_STATS_URL_TEMPLATE = 'https://fantasysports.yahooapis.com/fantasy/v2/team/{team_key}/roster/players/stats;type=week;week={week_number}'
TEAM_MATCHUP_WEEK_URL_TEMPLATE = 'https://fantasysports.yahooapis.com/fantasy/v2/team/{team_key}/matchups;type=week;week={week_number}'


def get_creds_from_aws():
    # set up AWS sso session 
    session = boto3.Session(profile_name='connor-ruff-dev-acct', region_name='us-east-2')
    sm_client = session.client('secretsmanager')
    secret_name = 'yahoo-fantasy--slop-api-keys'
    response = sm_client.get_secret_value(SecretId=secret_name)
    secret_string = response['SecretString']
    return json.loads(secret_string)

def get_access_token_from_refresh_token(refresh_token, client_id, client_secret):
    token_url = ACCESS_TOKEN_URL
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

def get_team_player_stats(team_key, week_number, access_token):
    url = TEAM_ROSTER_STATS_URL_TEMPLATE.format(team_key=team_key, week_number=week_number)
    headers = {
        'Authorization': f'Bearer {access_token}',
        'Accept': 'application/json'
    }
    resp = requests.get(url, headers=headers)
    if resp.status_code != 200:
        print('Error fetching team player stats:', resp.status_code, resp.text)
        raise Exception('Failed to fetch team player stats')
    
    resp_json = xmltodict.parse(resp.text)
    return resp_json

def get_team_matchup_stats(team_key, week_number, access_token):
    url = TEAM_MATCHUP_WEEK_URL_TEMPLATE.format(team_key=team_key, week_number=week_number)

    headers = {
        'Authorization': f'Bearer {access_token}',
        'Accept': 'application/json'
    }
    resp = requests.get(url, headers=headers)
    if resp.status_code != 200:
        print('Error fetching matchups:', resp.status_code, resp.text)
        raise Exception('Failed to fetch matchups')
        
    resp_json = xmltodict.parse(resp.text)
    return resp_json

def get_game_info(access_token):
    url = f'https://fantasysports.yahooapis.com/fantasy/v2/league/{LEAGUE_KEY}/players/stats/'
    headers = {
        'Authorization': f'Bearer {access_token}',
        'Accept': 'application/json'
    }
    resp = requests.get(url, headers=headers)
    if resp.status_code != 200:
        print('Error fetching game info:', resp.status_code, resp.text)
        raise Exception('Failed to fetch game info')
    
    resp_json = xmltodict.parse(resp.text)
    return resp_json



aws_creds = get_creds_from_aws()
access_token=get_access_token_from_refresh_token(
    refresh_token=aws_creds['refresh_token'],
    client_id=aws_creds['client_id'],
    client_secret=aws_creds['client_secret']
)

player_info = get_game_info(access_token)

with open('player_info.json', 'w') as f:
    json.dump(player_info, f, indent=4)

