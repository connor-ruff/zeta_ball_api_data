from auth import get_access_token_from_refresh_token
import requests
import xmltodict
import json

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

access_token = get_access_token_from_refresh_token(refresh_token='',
                                                                  client_id='',
                                                                  client_secret='')

stats = get_team_matchup_stats('466.l.6036.t.7', 4, access_token)

with open('tester_output_3.json', 'w') as f:
    json.dump(stats, f, indent=2)