import sys
import json
import re
from textblob import TextBlob
from pyspark import SparkContext
from pyspark.streaming import StreamingContext
from pyspark.mllib.clustering import StreamingKMeans
from collections import defaultdict

def clean_twitch_chat_message(message):
    # Remove usernames
    message = re.sub(r'@[\S]+', '', message)
    # Remove emotes
    message = re.sub(r':[a-z]+:', '', message)
    # Remove URLs
    message = re.sub(r'http\S+', '', message)
    # Remove punctuation and digits
    message = re.sub(r'[^\w\s]', '', message)
    message = re.sub(r'\d+', '', message)
    # Remove extra whitespace
    message = re.sub(r'\s+', ' ', message)
    # Remove leading/trailing whitespace
    message = message.strip()
    return message
    
def attach_sentiment(text): 

    # create a TextBlob object for the text
    blob = TextBlob(text)

    # get the sentiment polarity and subjectivity
    polarity = blob.sentiment.polarity

    return polarity

def get_sentiments_each_game(message):
    message =json.loads(message.strip(), strict=False)

    sentiments = defaultdict(list)
    for game_name, msg_string in message.items():
        msgs = msg_string.split('\r\n:')
        for msg in msgs:
            if 'PRIVMSG' in msg:
                msg = msg.split(':')[-1]
                msg = clean_twitch_chat_message(msg)
                sentiment = attach_sentiment(msg)
                sentiments[game_name].append(sentiment)
    return sentiments

def combine_sentiments(sentiments_a, sentiments_b):
    for game_name, sentiment_list in sentiments_b.items():
        sentiments_a[game_name].extend(sentiment_list)
    return sentiments_a

# Define the function to extract data from the JSON string and perform analysis
def process_stream(stream):
    stream = stream.window(60,1)
    sentiments_each_game = stream.map(get_sentiments_each_game)
    sentiments = sentiments_each_game.reduce(combine_sentiments)
    
    return sentiments

if __name__ == "__main__":
    if len(sys.argv) != 3:
        print("Usage: twitch_chat_analysis.py <hostname> <port>", file=sys.stderr)
        sys.exit(-1)
    sc = SparkContext(appName="TwitchChatAnalysis")
    sc.setLogLevel("ERROR")
    ssc = StreamingContext(sc, 1)

    stream = ssc.socketTextStream(sys.argv[1], int(sys.argv[2]))
    print('Content:')
    stream.pprint()

    # Process the stream
    sentiments = process_stream(stream)
    sentiments.pprint()

    ssc.start()
    ssc.awaitTermination()