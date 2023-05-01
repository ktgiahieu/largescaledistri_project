import sys
import json
import re
import os
import pandas as pd
from textblob import TextBlob
from pyspark import SparkContext
from pyspark.streaming import StreamingContext
from pyspark.mllib.clustering import StreamingKMeans
from collections import defaultdict
from pyspark.mllib.linalg import Vectors

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
    subjectivity = blob.sentiment.subjectivity

    return [polarity, subjectivity]

def get_sentiments(message):
    message =json.loads(message.strip(), strict=False)

    game_names = []
    sentiments = []
    for game_name, msg_string in message.items():
        msgs = msg_string.split('\r\n:')
        cleaned_msgs = []
        for msg in msgs:
            if 'PRIVMSG' in msg:
                msg = msg.split(':')[-1]
                msg = clean_twitch_chat_message(msg)
                cleaned_msgs.append(msg)
        msgs = '. '.join(cleaned_msgs)
        sentiment = attach_sentiment(msgs)
        game_names.append(game_name)
        sentiments.append(sentiment)
    return {'game': game_names[0], 'sentiment': sentiments[0]}

# Define the function to extract data from the JSON string and perform analysis
def process_stream(stream):
    stream = stream.window(60,1)
    sentiments = stream.map(get_sentiments)
    sentiments = sentiments.map(lambda x: ((x['game'], x['sentiment']), Vectors.dense(x['sentiment'])))
    return sentiments

def savePredictionsToCsv(rdd):
    # Convert RDD to DataFrame
    new_rows = []
    for pred in rdd.collect():
        (game, sentiment), prediction = pred
        new_rows.append([game, sentiment[0], sentiment[1], prediction])
    new_df = pd.DataFrame(new_rows, columns=['game', 'polarity', 'subjectivity', 'prediction'])

    new_df.to_csv('output.csv', index=False)

if __name__ == "__main__":
    if len(sys.argv) != 3:
        print("Usage: twitch_chat_analysis.py <hostname> <port>", file=sys.stderr)
        sys.exit(-1)
    sc = SparkContext(appName="TwitchChatAnalysis")
    sc.setLogLevel("ERROR")
    ssc = StreamingContext(sc, 1)

    stream = ssc.socketTextStream(sys.argv[1], int(sys.argv[2]))

    # Process the stream to get the sentiment associated with each game
    games_and_sentiments = process_stream(stream)

    model = StreamingKMeans(k=5, decayFactor=0.1).setRandomCenters(2, 0.01, 2023)
    training_data = games_and_sentiments.map(lambda x: x[1])
    model.trainOn(training_data)

    predictions = model.predictOnValues(games_and_sentiments)

    predictions.foreachRDD(savePredictionsToCsv)

    ssc.start()
    ssc.awaitTermination()