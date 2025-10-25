import json 
from utils import *

def lambda_handler(event, context):
    
    week_number = event['week_number']

    api_creds_obj = get_api_creds()
    access_token = get_access_token_from_refresh_token(
        refresh_token=api_creds_obj['refresh_token'],
        client_id=api_creds_obj['client_id'],
        client_secret=api_creds_obj['client_secret']
    )
    matchup_data = get_matchups_for_week(
        week_number=week_number, 
        access_token=access_token
    )
    drop_file_in_s3(
        data=matchup_data,
        bucket_name='connors-misc-blob-for-blobs',
        file_key=f'zeta_ball/week_{week_number}_matchups.json'
    )

    return {
        'statusCode': 200,
        'body': json.dumps("Matchup data fetched successfully."),
    }