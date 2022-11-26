# LoL-LCU-LobbyReveal
Python script that allow user to see the member of the team in champ select, and to send a message with the u.gg in the chat

## How to use
requirements: python
```
pip install lcu_driver
pip install riotwatcher
```
create a Riot Api key
https://developer.riotgames.com/
you need to past your api key line 20
```
api_key = '<RIOT API KEY>'
```

for create a LobbyReveal.exe 
```
pip install PyInstaller # if you don't have it
python3 -O -m PyInstaller LobbyReveal.py  --onefile -n LobbyReveal
``` 
the LobbyReveal.exe must be in ./dist/LobbyReveal.exe

or run normaly with python
```
python3 LobbyReveal.py
```