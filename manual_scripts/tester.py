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
    url = f'https://fantasysports.yahooapis.com/fantasy/v2/league/{LEAGUE_KEY}/players;start=25;count=25/stats;type=date;date=2025-12-25'
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



def yahoo_get(url, access_token):
    headers = {
        'Authorization': f'Bearer {access_token}',
        'Accept': 'application/json'
    }
    resp = requests.get(url, headers=headers)
    if resp.status_code != 200:
        print('Error calling Yahoo:', url, resp.status_code, resp.text)
        raise Exception('Yahoo request failed')
    return xmltodict.parse(resp.text)

def as_list(x):
    return x if isinstance(x, list) else [x]

def list_my_nba_leagues(access_token):
    """All NBA leagues the logged-in user has been in, across seasons (shows game_key + league_key)."""
    url = 'https://fantasysports.yahooapis.com/fantasy/v2/users;use_login=1/games;game_codes=nba/leagues'
    data = yahoo_get(url, access_token)
    games = as_list(data['fantasy_content']['users']['user']['games']['game'])
    for g in games:
        for lg in as_list(g['leagues']['league']):
            print(f"season={g['season']} game_key={g['game_key']} league_key={lg['league_key']} name={lg['name']}")

def get_league_teams(league_key, access_token):
    url = f'https://fantasysports.yahooapis.com/fantasy/v2/league/{league_key}/teams'
    data = yahoo_get(url, access_token)
    teams = as_list(data['fantasy_content']['league']['teams']['team'])
    out = {}
    for t in teams:
        mgrs = as_list(t['managers']['manager'])
        out[t['team_key']] = (t['name'], mgrs[0].get('nickname'))
    return out

def check_league_and_team_keys(access_token, league_key=LEAGUE_KEY, expected_team_keys=TEAM_KEYS):
    """Prints the league's current teams and diffs them against the TEAM_KEYS list in this file."""
    print(f'--- Teams in {league_key} ---')
    actual = get_league_teams(league_key, access_token)
    for k, (name, mgr) in sorted(actual.items(), key=lambda kv: int(kv[0].split('.t.')[1])):
        print(f'{k}  {name}  ({mgr})')
    expected = set(expected_team_keys)
    print('Missing from Yahoo:', sorted(expected - set(actual)) or 'none')
    print('Not in TEAM_KEYS:  ', sorted(set(actual) - expected) or 'none')


aws_creds = get_creds_from_aws()
access_token=get_access_token_from_refresh_token(
    refresh_token=aws_creds['refresh_token'],
    client_id=aws_creds['client_id'],
    client_secret=aws_creds['client_secret']
)

print('done')

# list_my_nba_leagues(access_token)
# check_league_and_team_keys(access_token)
