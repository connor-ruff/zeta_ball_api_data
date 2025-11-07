import requests
import xmltodict
import boto3
import json
from datetime import datetime, timedelta
from zoneinfo import ZoneInfo  # built into Python 3.9+
from constants import * 

def get_api_creds():
    client = boto3.client('secretsmanager', region_name='us-east-2')
    secret_name = 'yahoo-fantasy--slop-api-keys'
    response = client.get_secret_value(SecretId=secret_name)
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

def get_matchups_for_week(week_number, access_token):
    url = MATCHUP_WEEK_URL_TEMPLATE.format(league_key=LEAGUE_KEY, week_number=week_number)
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

def drop_file_in_s3(data, bucket_name, file_key):
    s3_client = boto3.client('s3')
    s3_client.put_object(
        Body=json.dumps(data),
        Bucket=bucket_name,
        Key=file_key
    )
    print(f'File dropped in S3 at s3://{bucket_name}/{file_key}')

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

def calculate_weeks_since_season_start():

    season_start_date = datetime.strptime(SEASON_START_WEEK, '%Y-%m-%d').date()
    eastern = ZoneInfo("America/New_York")
    now_eastern = datetime.now(eastern).date()

    delta_days = (now_eastern - season_start_date).days
    current_week_number = (delta_days // 7) + 1

    weeks_completed = current_week_number - 1

    return weeks_completed

    # get todays date on Eastern Time
