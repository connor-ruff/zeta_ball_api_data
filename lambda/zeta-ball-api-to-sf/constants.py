# FANTASY LEAGUE
LEAGUE_KEY = '466.l.6036'

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

