import json 
from utils import *

def lambda_handler(event, context):
    
    payload = json.loads(event["body"])["data"][0]
    team_key = payload[1]
    weeks_completed = payload[2]


    api_creds_obj = get_api_creds()
    access_token = get_access_token_from_refresh_token(
        refresh_token=api_creds_obj['refresh_token'],
        client_id=api_creds_obj['client_id'],
        client_secret=api_creds_obj['client_secret']
    )


    team_stats_data = get_team_player_stats(
            team_key, 
            weeks_completed, 
            access_token
    )

    drop_file_in_s3(
            data=team_stats_data,
            bucket_name='connors-misc-blob-for-blobs',
            file_key=f'zeta_ball/week_{weeks_completed}/team_stats/{team_key}_stats.json'
    )

    matchup_stats_data = get_team_matchup_stats(team_key, access_token)

    drop_file_in_s3(
            data=matchup_stats_data,
            bucket_name='connors-misc-blob-for-blobs',
            file_key=f'zeta_ball/week_{weeks_completed}/team_matchups/{team_key}_matchups.json'
    )

    return {
        "statusCode": 200,
        "body": json.dumps({

            "data": [
               [0, "SUCCESS"]
            ]
        })
    }