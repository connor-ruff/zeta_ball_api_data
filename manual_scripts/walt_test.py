import requests
import boto3
import json
import os

BASE_URL = 'https://www.zetaball.com/api/v1'
LEAGUE_ID = 'zeta_ball'
SECRET_NAME = 'zetaball-walter-api-key'
OUTPUT_DIR = os.path.join(os.path.dirname(__file__), 'walt_output')


def get_api_key():
    session = boto3.Session(profile_name='connor-ruff-dev-acct', region_name='us-east-2')
    sm_client = session.client('secretsmanager')
    secret_string = sm_client.get_secret_value(SecretId=SECRET_NAME)['SecretString']
    try:
        return json.loads(secret_string)['api_key']
    except (json.JSONDecodeError, KeyError):
        return secret_string


def call_endpoint(api_key, path, params=None):
    """GET {BASE_URL}{path} and return the parsed JSON. Prints error.fix/details on 4xx."""
    headers = {'Authorization': f'Bearer {api_key}', 'Accept': 'application/json'}
    resp = requests.get(BASE_URL + path, headers=headers, params=params)
    if resp.status_code != 200:
        print('Error calling', path, resp.status_code, resp.text)
        raise Exception(f'Failed to call {path}')
    return resp.json()


def dump_response(name, data):
    os.makedirs(OUTPUT_DIR, exist_ok=True)
    file_path = os.path.join(OUTPUT_DIR, f'{name}.json')
    with open(file_path, 'w') as f:
        json.dump(data, f, indent=2)
    print(f'Wrote {file_path}')


def dump_endpoint(api_key, name, path, params=None):
    dump_response(name, call_endpoint(api_key, path, params))


def dump_league_overview(api_key):
    """Who am I, what leagues, teams, settings, standings, rosters."""
    dump_endpoint(api_key, 'me', '/me')
    dump_endpoint(api_key, 'leagues', '/leagues')
    dump_endpoint(api_key, 'teams', f'/leagues/{LEAGUE_ID}/teams')
    dump_endpoint(api_key, 'settings', f'/leagues/{LEAGUE_ID}/settings')
    dump_endpoint(api_key, 'standings', f'/leagues/{LEAGUE_ID}/standings')
    dump_endpoint(api_key, 'rosters', f'/leagues/{LEAGUE_ID}/rosters')


def dump_matchups(api_key, season=2026, week=1):
    dump_endpoint(api_key, f'matchups_{season}_w{week}', f'/leagues/{LEAGUE_ID}/matchups',
                  {'season': season, 'week': week})
    dump_endpoint(api_key, f'week_report_{season}_w{week}', f'/leagues/{LEAGUE_ID}/weeks/report',
                  {'season': season, 'week': week})


def dump_history_and_activity(api_key):
    """Endpoints your Yahoo pull never gave you."""
    dump_endpoint(api_key, 'free_agents', f'/leagues/{LEAGUE_ID}/free-agents')
    dump_endpoint(api_key, 'transactions', f'/leagues/{LEAGUE_ID}/transactions')
    dump_endpoint(api_key, 'trades', f'/leagues/{LEAGUE_ID}/trades')
    dump_endpoint(api_key, 'draft_2025', f'/leagues/{LEAGUE_ID}/draft', {'season': 2025})
    dump_endpoint(api_key, 'manager_me', f'/leagues/{LEAGUE_ID}/managers/me')


def dump_transactions(api_key, season=2026, txn_type=None, since=None, limit=200):
    """League-wide adds, drops and trades, newest first (no manager filter).
    txn_type: 'add', 'drop', 'add/drop' or 'trade'. since: 'YYYY-MM-DD' (US Eastern). limit max 200."""
    params = {'season': season, 'limit': limit}
    if txn_type:
        params['type'] = txn_type
    if since:
        params['since'] = since
    name = f'transactions_{season}' + (f"_{txn_type.replace('/', '_')}" if txn_type else '')
    dump_endpoint(api_key, name, f'/leagues/{LEAGUE_ID}/transactions', params)


def dump_outlook(api_key, manager='me', window='14d'):
    """Live current-week matchup: each category now and projected to week's end, games left per side.
    manager: a manager id from /teams, or 'me'. window: '7d', '14d' or '30d' averages for the projection."""
    dump_endpoint(api_key, f'outlook_{manager}_{window}', f'/leagues/{LEAGUE_ID}/outlook',
                  {'manager': manager, 'window': window})


def main():
    api_key = get_api_key()
    print('API key retrieved successfully')
    #dump_league_overview(api_key)
    #dump_matchups(api_key)
    #dump_history_and_activity(api_key)
    #dump_transactions(api_key)
    dump_outlook(api_key)


if __name__ == '__main__':
    main()
