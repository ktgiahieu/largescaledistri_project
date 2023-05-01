# IMPORTANT:
# Open your favorite browser and go to (replace <your client id> with your client id):
# https://id.twitch.tv/oauth2/authorize?response_type=code&client_id=<your client id>&redirect_uri=http://localhost:3000&scope=chat%3Aread&state=c3ab8aa609ea11e793ae92361f002671
# Then, the browser will redirect you to a page to authorize your app. Click "Authorize" and you will be redirected to a page that looks like this:
# http://localhost:3000/?code=efsjbed1e387hq1icgnkghua33u0zn&scope=chat%3Aread&state=c3ab8aa609ea11e793ae92361f002671
# Copy your code (which is efsjbed1e387hq1icgnkghua33u0zn in this example) and paste it in the code variable below.
 

import requests

client_id = '9cgofwhhm5h8yzcc21gvp9aln86h8o'
client_secret = 'l1poku0ljhtuv9735nu3vrtcluynks'

body = {
    'client_id': client_id,
    'client_secret': client_secret,
    'code': 'qy95drslgjfke9ryrz489k4wkmvctz', # change this to your code
    "grant_type": 'authorization_code',
    "redirect_uri": 'http://localhost:3000'
}
r = requests.post('https://id.twitch.tv/oauth2/token', body)

#data output
keys = r.json();
print(keys)