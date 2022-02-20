from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
import os
from random import randint

def get_creds(scopes: list):
    """fetch google api client credentials.

    scopes must be a list of str containing the full scope
    urls requested by the client.
    """

    creds = None

    # if there are tokens stored in directory
    if os.path.exists('token.json'):
        creds = Credentials.from_authorized_user_file('token.json', scopes)

    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            # there is a refresh token, so refresh for a new valid token
            creds.refresh(Request())
        else:
            # begin user OAuth2 authentication using a local server strategy
            flow = InstalledAppFlow.from_client_secrets_file(
                'creds.json', scopes)
            creds = flow.run_local_server(port=0)

        with open('token.json', 'w') as f:
            f.write(creds.to_json())
            f.close()
            
    return creds


def clean_dir(fname=None, fdir=None):
    """deletes the file specified by fname
    and, optionally, the directory specified by fdir.
    """
    if fname:
        if os.path.exists(fname):
            os.remove(fname)
            
    if fdir:
        if os.path.exists(fdir):
            for file in os.listdir(fdir):
                os.remove(fdir+'/'+file)
            os.rmdir(fdir)


def generate_rand_diffname():
    """returns a random 2-word string of the form:
    ``Adjective`` + ``Noun``
    """
    adjectives = [
        'adorable',
        'agreeable',
        'bloody',
        'cute',
        'dead',
        'defeated',
        'curious',
        'faithful',
        'fantastic',
        'frail',
        'gleaming',
        'fancy',
        'fair',
        'exuberant',
        'grumpy',
        'horrible',
        'inexpensive',
        'homely',
        'grotesque',
        'gorgeous',
        'grieving',
        'good',
        'gifted',
        'lonely',
        'lucky',
        'naughty',
        'obnoxious',
        'obedient'
    ]

    nouns = [
        'airplane',
        'bycicle',
        'jaguar',
        'computer',
        'biscuit',
        'hitcircle',
        'slider',
        'spinner',
        'combo',
        'bottle',
        'beetle',
        'bunny',
        'fox',
        'horse',
        'cow',
        'system',
        'star',
        'planet',
        'galaxy',
        'monkey',
        'gorilla',
        'tail',
        'rack',
        'mountain',
        'volcano',
        'boy',
        'girl',
        'software',
        'government'
    ]

    adj = adjectives[randint(0, len(adjectives)-1)]
    noun = nouns[randint(0, len(nouns)-1)]

    return adj.capitalize() + noun.capitalize()