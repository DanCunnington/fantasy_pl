"""
Functions to manage CRUD operations on fantasy.premierleague.com.
"""
import urllib.parse
import requests
import constants

# Create a session - this persists cookies across requests
MY_SESSION = requests.Session()

def get_deadline():
    """
    Get the next deadline for submitting transfers/team choice
    """
    dynamic_data = MY_SESSION.get(constants.FANTASY_API_DYNAMIC_URL).json()
    return dynamic_data['next_event_fixtures'][0]['deadline_time']

def get_transfers_squad():
    """
    Get the current selected squad from the transfers page.
    This gives more information about transfers, such as selling price.
    Note: must be logged in first!
    """
    print('Getting current squad...')
    squad_request_headers = {
        'X-Requested-With': 'XMLHttpRequest'
    }
    return MY_SESSION.get(constants.TRANSFER_URL, headers=squad_request_headers).json()

def grab_all():
    """
    Grab all the json data from the fantasy api url.
    """
    return MY_SESSION.get(constants.FANTASY_API_URL).json()

def grab_player_fixtures(player_id):
    """
    Grab a single player's full history and fixture list using their id.
    """
    return MY_SESSION.get(constants.FANTASY_PLAYER_API_URL + str(player_id)).json()

def login(username, password):
    """
    Login to the fantasy football web app.
    """
    print('Logging in...')

    # Make a GET request to users.premierleague.com to get the correct cookies
    MY_SESSION.get(constants.LOGIN_URL)
    csrf_token = MY_SESSION.cookies.get('csrftoken', domain='users.premierleague.com')

    # POST to the users url with the login credentials and csrfcookie
    login_data = urllib.parse.urlencode({
        'csrfmiddlewaretoken': csrf_token,
        'login': username,
        'password': password,
        'app': 'plusers',
        'redirect_uri': 'https://users.premierleague.com/'
    })

    login_headers = {
        'Content-Type': 'application/x-www-form-urlencoded'
    }

    result = MY_SESSION.post(constants.LOGIN_URL, headers=login_headers, data=login_data)
    if result.status_code != 200:
        print(result)
        print(result.text)

    # Make a GET request to fantasy.premierleague.com to get the correct cookies
    MY_SESSION.get(constants.FANTASY_URL)
    dynamic_data = MY_SESSION.get(constants.FANTASY_API_DYNAMIC_URL).json()
    constants.NEXT_EVENT = dynamic_data['next-event']
    constants.SQUAD_ID = dynamic_data['entry']['id']
    constants.SQUAD_URL += str(constants.SQUAD_ID) + '/'
    constants.TRANSFER_DEADLINE = dynamic_data['next_event_fixtures'][0]['deadline_time']

def calculate_transfers(old_squad, new_squad):
    """
    Given lists containing the old(/current)_squad and the new_squad,
    calculate the new transfers object.
    """
    print('Creating transfers object...')

    # Create our transfers object and players_in/out lists
    new_squad_ids = [player['id'] for player in new_squad]
    old_squad_ids = [player['element'] for player in old_squad]
    players_in = [player for player in new_squad if player['id'] not in old_squad_ids]
    players_out = [player for player in old_squad if player['element'] not in new_squad_ids]
    transfer_object = {
        'confirmed': 'true',
        'entry': constants.SQUAD_ID,
        'event': constants.NEXT_EVENT,
        'transfers': [],
        'wildcard': 'false'
    }

    # We sort the players_in list by player_type as each transfer must be of the same type
    # players_out should already be sorted
    players_in = sorted(players_in, key=lambda player: (player['element_type']))

    # for each player_in/player_out create a transfer
    for i in range(len(players_in)):
        transfer_object['transfers'].append({
            'element_in': players_in[i]['id'],
            'purchase_price': players_in[i]['now_cost'],
            'element_out': players_out[i]['element'],
            'selling_price': players_out[i]['selling_price']
        })
    print(transfer_object)
    return transfer_object

def make_transfers(transfer_object):
    """
    Given a transfers object, make the corresponding transfers in the webapp.
    """
    print('Making transfers...')

    # if we need to make transfers, then do so and return the response object
    # else return a generic success response (since we didn't need to do anything!)
    if len(transfer_object['transfers']) > 0:
        MY_SESSION.get('https://fantasy.premierleague.com/a/squad/transfers')
        csrf_token = MY_SESSION.cookies.get('csrftoken', domain='fantasy.premierleague.com')

        transfer_headers = {
            'X-CSRFToken': csrf_token,
            'X-Requested-With': 'XMLHttpRequest',
            'Referer': 'https://fantasy.premierleague.com/a/squad/transfers'
        }

        result = MY_SESSION.post(
            constants.TRANSFER_URL,
            headers=transfer_headers,
            json=transfer_object
        )

        if result.status_code != 200:
            print(result)
            print(result.text)
        return result
    else:
        response_success = requests.Response
        response_success.status_code = 200
        return response_success

def set_starting_lineup(starting_lineup):
    """
    Set the starting lineup correctly in the webapp.
    """
    print('Adjusting starting lineup...')

    # Make a GET request to get the correct cookies
    MY_SESSION.get(constants.SQUAD_URL)
    csrf_token = MY_SESSION.cookies.get('csrftoken', domain='fantasy.premierleague.com')

    starting_lineup_headers = {
        'X-CSRFToken': csrf_token,
        'X-Requested-With': 'XMLHttpRequest',
        'Referer': 'https://fantasy.premierleague.com/a/team/my'
    }

    result = MY_SESSION.post(
        constants.SQUAD_URL,
        headers=starting_lineup_headers,
        json=starting_lineup
    )

    if result.status_code != 200:
        print(result)
        print(result.text)
    return result
