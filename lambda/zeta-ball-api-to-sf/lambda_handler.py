import json 
from utils import *

def lambda_handler(event, context):
    
    weeks_completed = calculate_weeks_since_season_start()

    api_creds_obj = get_api_creds()
    access_token = get_access_token_from_refresh_token(
        refresh_token=api_creds_obj['refresh_token'],
        client_id=api_creds_obj['client_id'],
        client_secret=api_creds_obj['client_secret']
    )

    # Pull Matchup Data
    matchup_data = get_matchups_for_week(
        week_number=weeks_completed, 
        access_token=access_token
    )
    drop_file_in_s3(
        data=matchup_data,
        bucket_name='connors-misc-blob-for-blobs',
        file_key=f'zeta_ball/week_{weeks_completed}/matchups.json'
    )

    # Pull team stat data
    for team_key in TEAM_KEYS:

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

    return {
        'statusCode': 200,
        'body': json.dumps("Matchup data fetched successfully."),
        'weeks_completed': weeks_completed
    }