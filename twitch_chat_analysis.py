import sys
import json
from textblob import TextBlob
from pyspark import SparkContext
from pyspark.streaming import StreamingContext
from pyspark.mllib.clustering import StreamingKMeans

# import spacy

# nlp = spacy.load("en_core_web_sm")
topics = []
def get_all_words(msg):
    """Processes the messages to extract relevant keywords"""
    # Extract keywords using Named Entity Recognition
    doc = TextBlob(msg)
    all_words = list(set([w for w in doc.words]))
    return all_words

# def get_keywords(msg):
#     """Processes the messages to extract relevant keywords"""
#     # Extract keywords using Named Entity Recognition
#     doc = nlp(msg)
#     keywords = [ent.text for ent in doc.ents if ent.label_ == "ORG" or ent.label_ == "PERSON" or ent.label_ == "GPE"]
#     return keywords

# # Define the function to perform sentiment analysis
# def get_sentiment(message):
#     text = message
#     blob = TextBlob(text)
#     sentiment = blob.sentiment.polarity
#     return (sentiment, message)

# def sentiment_cluster(msg):
#         try:
#             sentiment = TextBlob(msg).sentiment.polarity
#             if sentiment > 0.5:
#                 return "Positive"
#             elif sentiment < -0.5:
#                 return "Negative"
#             else:
#                 return "Neutral"
#         except:
#             return "Error"

# # Define the function to get the location of the user
# def get_location(message):
#     user = message['user']
#     if 'location' in user:
#         location = user['location']
#     else:
#         location = 'Unknown'
#     return (location, message)

# Define the function to perform clustering
def do_clustering(topics):
    if len(topics) > 0:
        # Convert the topics to a numerical vector using one-hot encoding
        vocab = list(set(topics))
        vector = [int(topic in topics) for topic in vocab]
        
        # Initialize the streaming k-means model
        model = StreamingKMeans(k=3, decayFactor=0.5)
        # Update the streaming k-means model with the vector
        model.update([vector])
        
        # Get the current centroids of the model
        centroids = model.latestModel().clusterCenters.tolist()
        
        # Emit the current centroids
        yield centroids

# Define the function to extract data from the JSON string and perform analysis
def process_stream(stream):
    stream  = stream.window(60, 1)
    messages = stream.filter(lambda x: "PRIVMSG" in x).map(lambda x: x.split(':')[-1])
    all_words = messages.map(get_all_words).reduce(lambda a, b: a + b)
    return all_words
    # centroids = topics.flatMap(do_clustering)

    # # location = sentiment.map(get_location)
    # # labels = do_clustering(location)
    # # window_counts = labels.countByValueAndWindow(60, 1)
    # # print(window_counts)
    # if len(topics) > 0:
    #     # Convert the topics to a numerical vector using one-hot encoding
    #     vocab = list(set(topics))
    #     vector = [int(topic in topics) for topic in vocab]
        
    #     # Initialize the streaming k-means model
    #     model = StreamingKMeans(k=3, decayFactor=0.5)
    #     # Update the streaming k-means model with the vector
    #     model.update([vector])
        
    #     # Get the current centroids of the model
    #     centroids = model.latestModel().clusterCenters.tolist()
        
    #     # Emit the current centroids
    #     yield centroids


if __name__ == "__main__":
    if len(sys.argv) != 3:
        print("Usage: twitch_chat_analysis.py <hostname> <port>", file=sys.stderr)
        sys.exit(-1)
    sc = SparkContext(appName="TwitchChatAnalysis")
    sc.setLogLevel("WARN")
    ssc = StreamingContext(sc, 1)
    ssc.checkpoint("checkpoint")

    # Define the parameters for the StreamingKMeans model
    num_clusters = 5
    decay_factor = 0.5

    stream = ssc.socketTextStream(sys.argv[1], int(sys.argv[2]))
    # stream.pprint()
    centroids = process_stream(stream)

    
    # Print the centroids to the console
    centroids.pprint()

    ssc.start()
    ssc.awaitTermination()