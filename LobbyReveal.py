import sys
import requests
from urllib3 import disable_warnings
import json
from time import sleep
import platform
import psutil
import base64
from os import system, name
from lcu_driver import Connector
from riotwatcher import LolWatcher, ApiError


disable_warnings()

# global variables

api_key = 'RGAPI-xxxxxxxx-xxxx-xxxx-xxxx-xxxxxxxxxxxx'
watcher = LolWatcher(api_key)
my_region = 'euw1'

app_port = None
auth_token = None
riotclient_auth_token = None
riotclient_app_port = None
region = None
lcu_name = None   # LeagueClientUx executable name
showNotInChampSelect = True

# functions


def getLCUName():
    '''
    Get LeagueClient executable name depending on platform.
    '''
    global lcu_name
    if platform.system() == 'Windows':
        lcu_name = 'LeagueClientUx.exe'
    elif platform.system() == 'Darwin':
        lcu_name = 'LeagueClientUx'
    elif platform.system() == 'Linux':
        lcu_name = 'LeagueClientUx'


def LCUAvailable():
    '''
    Check whether a client is available.
    '''
    return lcu_name in (p.name() for p in psutil.process_iter())


def getLCUArguments():
    global auth_token, app_port, region, riotclient_auth_token, riotclient_app_port
    '''
    Get region, remoting-auth-token and app-port for LeagueClientUx.
    '''
    if not LCUAvailable():
        sys.exit('No ' + lcu_name + ' found. Login to an account and try again.')

    for p in psutil.process_iter():
        if p.name() == lcu_name:
            args = p.cmdline()

            for a in args:
                if '--region=' in a:
                    region = a.split('--region=', 1)[1].lower()
                if '--remoting-auth-token=' in a:
                    auth_token = a.split('--remoting-auth-token=', 1)[1]
                if '--app-port' in a:
                    app_port = a.split('--app-port=', 1)[1]
                if '--riotclient-auth-token=' in a:
                    riotclient_auth_token = a.split('--riotclient-auth-token=', 1)[1]
                if '--riotclient-app-port=' in a:
                    riotclient_app_port = a.split('--riotclient-app-port=', 1)[1]

                    
def clear():
    # for windows
    if name == 'nt':
        _ = system('cls')
    # for mac and linux(here, os.name is 'posix')
    else:
        _ = system('clear')


connector = Connector()
@connector.ready

async def connect(connection):
    
    global showNotInChampSelect

    getLCUName()

    getLCUArguments()

    lcu_api = 'https://127.0.0.1:' + app_port
    riotclient_api = 'https://127.0.0.1:' + riotclient_app_port

    lcu_session_token = base64.b64encode(
        ('riot:' + auth_token).encode('ascii')).decode('ascii')

    riotclient_session_token = base64.b64encode(
        ('riot:' + riotclient_auth_token).encode('ascii')).decode('ascii')

    lcu_headers = {
        'Content-Type': 'application/json',
        'Accept': 'application/json',
        'Authorization': 'Basic ' + lcu_session_token
    }

    riotclient_headers = {
        'Content-Type': 'application/json',
        'Accept': 'application/json',
        'User-Agent': 'LeagueOfLegendsClient',
        'Authorization': 'Basic ' + riotclient_session_token
    }

    get_current_summoner = lcu_api + '/lol-summoner/v1/current-summoner'

    r = requests.get(get_current_summoner, headers=lcu_headers, verify=False)
    r = json.loads(r.text)
    print("Welcome to the League of Legends Party name finder :)!")
    print('Connected: ' + r['displayName'])

    try :
        checkForLobby = True
        while True:
            nameArr = []
            get_champ_select = lcu_api + '/lol-champ-select/v1/session'
            r = requests.get(get_champ_select, headers=lcu_headers, verify=False)
            r = json.loads(r.text)
            if 'errorCode' in r:
                checkForLobby = True
                if showNotInChampSelect:
                    print('Not in champ select. Waiting for game...')
                    showNotInChampSelect = False
            else:
                if checkForLobby:
                    clear()
                    print('\n* Found lobby. *\n')
                    while 1:
                        try:
                            get_lobby = riotclient_api + '/chat/v5/participants/champ-select'
                            r = requests.get(get_lobby, headers=riotclient_headers, verify=False)
                            r = json.loads(r.text)
                        except:
                            print("la route n'existe plus, logiciel obselète")
                        nameArr = [] 
                        nospaces = []
                        ranked_stats = []
                        totalWinrate = 0
                        nbPlayer = 5
                        elo = ""
                        rank = ""
                        try:
                            getChat = await connection.request('get', "/lol-chat/v1/conversations")
                            chat = await getChat.json()
                        except KeyError:
                            print("error in get conversation")
                        for i in range(len(chat)):
                            if chat[i]['type'] == "championSelect":
                                try:
                                    lobbyID = chat[i]["id"]
                                except KeyError:
                                    print("error in get lobby id")
                                headers = {'Content-type': 'application/json'}
                                request = "/lol-chat/v1/conversations/" + str(lobbyID) + "/messages"
                                for x in r['participants']:
                                    nameArr.append(x['game_name'])
                                    nospaces.append(x['game_name'].replace(" ", "%20"))
                                print(len(nameArr))
                                if len(nameArr) == nbPlayer:
                                    for i in range(len(nameArr)):
                                        try:
                                            usera = watcher.summoner.by_name(my_region, nameArr[i])
                                            #sleep(0.3)
                                            user_id = usera['id']
                                            #print(nameArr[i], " : ", user_id)
                                           
                                            try: 
                                                ranked_stats = watcher.league.by_summoner(my_region, user_id)
                                                #print(ranked_stats)
                                                for j in range(len(ranked_stats)):
                                                    try:
                                                        if ranked_stats[j]['queueType'] == "RANKED_SOLO_5x5":
                                                            elo = ranked_stats[j]['tier']
                                                            rank = ranked_stats[j]['rank']
                                                            win = ranked_stats[j]['wins']
                                                            lose = ranked_stats[j]['losses']
                                                            winrate = win / (win + lose)
                                                            totalWinrate += winrate
                                                            print(nameArr[i], " : ", rank, elo, winrate)
                                                            winrate = win / (win + lose) * 100
                                                            gameNbr = win + lose
                                                            totalWinrate = totalWinrate + winrate                
                                                            await connection.request('post', request, headers=headers, data={"type":"chat", "body": str(nameArr[i]) + " is " + str(elo) + " " + str(rank) + " with a " + str(round(winrate,2)) + "% winrate in " + str(gameNbr) + " games."})
                                                    except KeyError:
                                                        await connection.request('post', request, headers=headers, data={"type":"chat", "body": "error getting " + str(nameArr[i]) + " ranked datas, first game ? "})
                                            except ApiError:
                                                print("error in get ranked stats")
                                                await connection.request('post', request, headers=headers, data={"type":"chat", "body": "error getting " + str(nameArr[i]) + " ranked datas :'("}) 
                                        except ApiError:
                                            print("error in get user id. check your api key ?")
                                            await connection.request('post', request, headers=headers, data={"type":"chat", "body": "error getting " + str(nameArr[i]) + " user id :'("})
                                    await connection.request('post', request, headers=headers, data={"type":"chat", "body": "https://euw.op.gg/multi/query=" + nospaces[0] + "%2C" + nospaces[1] + "%2C" + nospaces[2] + "%2C" + nospaces[3] + "%2C" + nospaces[4]})
                                    await connection.request('post', request, headers=headers, data={"type":"chat", "body": "Github: NoeMoyen"})
                                    await connection.request('post', request, headers=headers, data={"type":"chat", "body": "Please rate my homemade bot from 0 to 10, and if you have any idea, please let me know :)"})
                                    showNotInChampSelect = True
                                    checkForLobby = True 

                                    exit(0)   
                                #showNotInChampSelect = False
                                #checkForLobby = True
                                    
    except KeyboardInterrupt:
        print('\n\n* Exiting... *')
        sys.exit(0)

connector.start()