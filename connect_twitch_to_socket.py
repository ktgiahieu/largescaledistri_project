import requests
import socket
import time

client_id = 'rjc7kj7rpgurrxgizb1etjtqjcxg5l'
client_secret = 'dzx9k0ucr0ackq4j1ze14bmn65re42'
streamer_name = 'chess'

# keys obtained from get_access_token.py
keys = {'access_token': 'er5ts4nvh3r90xwb6ntxhuow6hy74h', 'expires_in': 13699, 'refresh_token': 'xdv4nms68mzgxv1yeg9xnj7h7swv6tm8q0ygcxelb40dg2ng1l', 'scope': ['chat:read'], 'token_type': 'bearer'}

headers = {
    'Client-ID': client_id,
    'Authorization': 'Bearer ' + keys['access_token']
}


stream = requests.get('https://api.twitch.tv/helix/streams?user_login=' + streamer_name, headers=headers)

stream_data = stream.json()

if len(stream_data['data']) == 1:
    print(streamer_name + ' is live: ' + stream_data['data'][0]['title'] + ' playing ' + stream_data['data'][0]['game_name'])
else:
    print(streamer_name + ' is not live');


server = 'irc.chat.twitch.tv'
port = 6667
nickname = 'thewonderwander'
token = f"oauth:{keys['access_token']}"
channel = f'#{streamer_name}'


sock = socket.socket()
sock.connect((server, port))

sock.send(f"PASS {token}\n".encode('utf-8'))
sock.send(f"NICK {nickname}\n".encode('utf-8'))
sock.send(f"JOIN {channel}\n".encode('utf-8'))

resp = sock.recv(2048).decode('utf-8')
print(resp)
resp = sock.recv(2048).decode('utf-8')
print(resp)

# sock.close()

# create a listening socket object
listening_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
listening_socket.bind(('localhost', 9999))
# listen for incoming connections
listening_socket.listen(1)
# accept incoming connections
client_socket, _ = listening_socket.accept()
print("✅ Listening socket created at localhost:9999")


# # create a socket to send messages to localhost 9999
# client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
# client_socket.connect(('127.0.0.1', 9999))

# # while KeyboardInterrupt is not pressed, continue to listen to chat
# # else, close the socket
try:
    while True:
        # sleep 1 second to avoid rate limiting
        time.sleep(1/60)
        resp = sock.recv(2048)
        
        # send received message to localhost 9999
        client_socket.send(resp)
        
except KeyboardInterrupt:
    sock.close()
    client_socket.close()
    listening_socket.close()
    print('Sockets closed')