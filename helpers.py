from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google.oauth2 import service_account as sva
from google_auth_oauthlib.flow import InstalledAppFlow
import os
from random import randint
from json import load, dump
from discord.ext.commands import Context

def get_creds_server(scopes: list):
    """fetch google api client credentials using
    service account keys.
    
    scopes must be a list of str containing the full scope
    urls requested by the client.
    """

    return sva.Credentials.from_service_account_file("service_acc_keys.json", scopes=scopes)



def get_creds_desktop(scopes: list):
    """fetch google api client credentials.

    scopes must be a list of str containing the full scope
    urls requested by the client.

    This function is currently unused but I'm gonna keep it around
    in case it becomes useful in near-future development
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


def load_configs():
    """load configurations"""

    try:
        with open("config.json", 'r', encoding='utf-8') as f:
            return load(f)
    except FileNotFoundError:
        return {}


def save_configs(configs: dict):
    """save configs by writing to
    disk
    """
    with open("config.json", 'w', encoding='utf-8') as f:
        dump(configs, f, indent=4)

def command_authorized(ctx: Context, parent_guild_id: int, auth_role_id: int):
    """This is a check to see if the user invoking a bot command
    is authorized to do so (are they a contest organizer?)
    
    Returns ``True`` for 'yes' and ``False`` for 'no'."""

    # get the guild of the invocation context, if it exists
    guild = ctx.guild
    if guild is None:
        # invokation was attempted through DMs (invalid)
        return False
    if guild.id != parent_guild_id:
        # invokation was attempted from an incorrect guild (invalid)
        return False

    user_roles = ctx.author.roles

    # check to see if the user invoking the command has the appropriate
    #  role
    for role in user_roles:
        if role.id == auth_role_id:
            return True
    return False
    





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
        'bicycle',
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