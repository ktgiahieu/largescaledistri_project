import requests
import socket
import time
import json
import os
from collections import defaultdict

# -------------- STEP 1: Initialize current Twitch account ---------------
# If this is not the first login, read the nickname, client id and client secret from file json
if 'twitch_info.json' in os.listdir():
    with open('twitch_info.json', 'r') as f:
        twitch_info = json.load(f)
    nickname = twitch_info['nickname']
    client_id = twitch_info['client_id']
    client_secret = twitch_info['client_secret']

# This is the first time login
else: 
    print('-'*50)
    print('First time login recogized, please enter your Twitch account information:')
    print('PLEASE ENTER YOUR TWITCH USERNAME:')
    nickname = input()
    print('Follow the instructions from https://dev.twitch.tv/docs/authentication/register-app/ to register your app and get your client id and client secret.')
    print('PLEASE ENTER YOUR CLIENT ID:')
    client_id = input()
    print('PLEASE ENTER YOUR CLIENT SECRET:')
    client_secret = input()
    # save the nickname, client id and client secret to file json
    with open('twitch_info.json', 'w') as f:
        json.dump({'nickname': nickname, 'client_id': client_id, 'client_secret': client_secret}, f)

# ------------ STEP 2: Get access token for chat:read scope ------------
try:
    # Test if the access token is still valid
    keys = json.load(open('oauth-keys.json', 'r'))
    headers = {
        'Client-ID': client_id,
        'Authorization': 'Bearer ' + keys['access_token']
    }
    stream = requests.get('https://api.twitch.tv/helix/streams?language=en&type=live&game_id=33214' , headers=headers)
    stream_data = stream.json()
    # check if we can get the stream data
    stream_data['data']
    # if not, we will need to get a new access token
except:
    print('-'*50)
    print('Authorization code expired !!')
    print('PLEASE GO TO YOUR BROWSER AND GET YOUR CODE FROM THE URL')
    print(f'https://id.twitch.tv/oauth2/authorize?response_type=code&client_id={client_id}&redirect_uri=http://localhost:3000&scope=chat%3Aread&state=c3ab8aa609ea11e793ae92361f002671')
    print('YOU WILL SEE YOUR CODE IN THE FORM')
    print('http://localhost:3000/?code=<YOUR CODE HERE>&scope=chat%3Aread&state=c3ab8aa609ea11e793ae92361f002671')
    print('PLEASE PASTE YOUR CODE BELOW:')
    code = input()

    body = {
        'client_id': client_id,
        'client_secret': client_secret,
        'code': code,
        "grant_type": 'authorization_code',
        "redirect_uri": 'http://localhost:3000'
    }
    r = requests.post('https://id.twitch.tv/oauth2/token', body)
    keys = r.json()

    # write oauth keys to file
    with open('oauth-keys.json', 'w') as f:
        json.dump(keys, f)


# ------------ STEP 3: Get current live streamers ------------
print('-'*50)

# For each of these games, get the top 5 live streamers
games = [
    'fortnite', 
    'Just%20Chatting', 
    'chess', 
    'valorant', 
    'Counter-Strike%3A%20Global%20Offensive'
]

headers = {
    'Client-ID': client_id,
    'Authorization': 'Bearer ' + keys['access_token']
}
with open('game_id.json', 'r') as f:
    game_id = json.load(f)

live_streams = {}
print('Current live streamers:')
for g_name in games:
    # If we already have the game id, use it
    if g_name in game_id:
        g_id = game_id[g_name]

    # If not, get the game id and save it to file
    else:
        game = requests.get('https://api.twitch.tv/helix/games?name=' + g_name, headers=headers)
        g_id = game.json()['data'][0]['id']
        game_id[g_name] = g_id

    stream = requests.get('https://api.twitch.tv/helix/streams?language=en&type=live&game_id=' + g_id, headers=headers)
    stream_data = stream.json()['data'][:1]
    streamer_name = [x['user_login'] for x in stream_data]
    live_streams[g_name] = streamer_name
    print(f'- {g_name}: {streamer_name}')

# ------------ STEP 4: Connect to Twitch IRC ------------
print('-'*50)

server = 'irc.chat.twitch.tv'
port = 6667
token = f"oauth:{keys['access_token']}"

sockets = {}
for g_name in games:
    print(f'Connecting to {g_name} chatroom')
    for streamer in live_streams[g_name]:
        # create a socket object
        sock = socket.socket()
        # connect to the server
        sock.connect((server, port))
        # send a message to server
        sock.send(f"PASS {token}\n".encode('utf-8'))
        sock.send(f"NICK {nickname}\n".encode('utf-8'))
        sock.send(f"JOIN #{streamer}\n".encode('utf-8'))
        sock.recv(2048).decode('utf-8')
        sock.recv(2048).decode('utf-8')
        # save the socket object
        sockets[streamer] = sock
        print(f"✅ Connected to {streamer}'s chatroom")

# ------------ STEP 5: Listen to chat messages ------------
print('-'*50)

# create a listening socket object
listening_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
listening_socket.bind(('localhost', 9999))
# listen for incoming connections
listening_socket.listen(1)
# accept incoming connections
print("Waiting for Spark Streaming client to connect...")
client_socket, _ = listening_socket.accept()
print("✅ Listening socket created at localhost:9999")


# while KeyboardInterrupt is not pressed, continue to listen to chat messages
try:
    while True:
        # sleep to avoid rate limiting
        time.sleep(1/20)
        for g_name in games:
            all_messages = defaultdict(list)
            for streamer in live_streams[g_name]:
                # get the socket object
                sock = sockets[streamer]
                # get the message from the socket
                resp = sock.recv(2048).decode('utf-8', 'ignore')
                all_messages[g_name].append(resp)

            # concatenate all messages
            all_messages[g_name] = ''.join(all_messages[g_name])
            print(f"{g_name}:\n{all_messages[g_name]}")
            # send the message to Spark Streaming
            client_socket.sendall((json.dumps(all_messages) + '\n').encode('utf-8'))
            

        
        
except (KeyboardInterrupt, BrokenPipeError) as e:
    if isinstance(e, BrokenPipeError):
        print('BrokenPipeError detected, closing sockets')
    elif isinstance(e, KeyboardInterrupt):
        print('KeyboardInterrupt detected, closing sockets')
    # close all sockets
    for g_name in games:
        for streamer in live_streams[g_name]:
            sockets[streamer].close()
    client_socket.close()
    listening_socket.close()
    print('Sockets closed')

