import requests
import socket
import time

client_id = 'rjc7kj7rpgurrxgizb1etjtqjcxg5l'
client_secret = 'dzx9k0ucr0ackq4j1ze14bmn65re42'
streamer_name = 'lestream'

# keys obtained from get_access_token.py
keys = {'access_token': 'hoqrxu5v6r46b5uihgddga1vcdjo35', 'expires_in': 13144, 'refresh_token': '5ldpdhs7mrpmh28eg60o9jp6oam8dlr7pt34onmh6gaqcoh6gl', 'scope': ['chat:read'], 'token_type': 'bearer'}

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

sock.close()

# # create a listening socket object
# listening_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
# listening_socket.bind(('localhost', 9999))
# # listen for incoming connections
# listening_socket.listen(1)
# # accept incoming connections
# connection, client_address = listening_socket.accept()


# # create a socket to send messages to localhost 9999
# client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
# client_socket.connect(('127.0.0.1', 9999))

# # while KeyboardInterrupt is not pressed, continue to listen to chat
# # else, close the socket
# try:
#     while True:
#         # sleep 1 second to avoid rate limiting
#         time.sleep(1)
#         resp = sock.recv(2048).decode('utf-8')
#         print(resp)
        
#         # send received message to localhost 9999
#         client_socket.send(resp.encode('utf-8'))
        
# except KeyboardInterrupt:
#     sock.close()
#     client_socket.close()
#     # listening_socket.close()
#     print('Sockets closed')