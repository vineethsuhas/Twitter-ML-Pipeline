import logging

import pandas as pd
from django.conf import settings
from elasticsearch import Elasticsearch

from services.utils import compute_nrc, pre_process


logger = logging.getLogger(settings.EC_LOG)


def get_emotions(tweets):
    # Get the NRC-Lexicon
    nrc_data = compute_nrc()

    # Tweets with emotions:
    emotions = {}

    # Tweets with no emotions:
    no_emotions = []

    for tweet_id, tweet in tweets.items():
        final_words = pre_process(tweet["text"])
        total_em = None
        for word in final_words:
            try:
                em = nrc_data.loc[word, :]
            except KeyError:
                # logger.debug("{0} DoesNotExist in NRC-Lexicon".format(word))
                continue
            total_em = total_em + em if isinstance(total_em, pd.Series) else em
        if isinstance(total_em, pd.Series):
            final_dict = total_em.to_dict()
            final_dict["tweet_text"] = tweet["text"]
            final_dict["collection_source"] = tweet["collection_source"]
            emotions[tweet_id] = final_dict
        else:
            no_emotions.append(tweet_id)
    return emotions, no_emotions


def get_es_query(online=True):
    if online:
        query = """
            {
              "query": {
                "bool": {
                  "must": [
                    {
                      "match": {
                        "lang": "en"
                      }
                    }
                  ],
                  "must_not": [],
                  "should": []
                }
              },
              "from": 0,
              "size": 2000,
              "sort": [],
              "aggs": {}
            }
            """
    else:
        query = """
            {
              "query": {
                "bool": {
                  "must": [
                    {
                      "match": {
                        "tweet_language": "en"
                      }
                    }
                  ],
                  "must_not": [],
                  "should": []
                }
              },
              "from": 0,
              "size": 1000,
              "sort": [],
              "aggs": {}
            }
            """
    return query


# def extract_tweet_emotions():
#     es = Elasticsearch()
#     tweet_text = {}
#
#     # Process ONLINE data:
#     online_query = get_es_query()
#     es_data = es.search(online_query, "online_index")
#     hits = es_data["hits"]["hits"]
#     for hit in hits:
#         tweet = hit["_source"]
#         tweet_text[tweet['id']] = {"text": tweet["text"], "collection_source": "online"}
#
#     # Process
#     offline_query = get_es_query(online=False)
#     es_data = es.search(offline_query, "offline_index")
#     hits = es_data["hits"]["hits"]
#     for hit in hits:
#         tweet = hit["_source"]
#         tweet_text[tweet['tweetid']] = {"text": tweet["tweet_text"], "collection_source": "offline"}
#
#     emotion_tweets, no_emotion_tweets = get_emotions(tweet_text)
#
#     for tweet_id, emotions in emotion_tweets.items():
#         logger.debug("Loading the emotions of tweet {0} into elasticsearch".format(tweet_id))
#         es.index('emotions', emotions, id=tweet_id)


def extract_tweet_emotions():
    """
    Scrolling API to retrieve emotions from ElasticSearch
    :return:
    """
    # ES Init
    es = Elasticsearch()

    # Process ONLINE data:
    online_query = get_es_query()

    # Init scroll by search
    data = es.search(
        index="online_index",
        scroll='2m',
        size=1000,
        body=online_query
    )

    # Get the scroll ID
    sid = data['_scroll_id']
    scroll_size = len(data['hits']['hits'])
    logger.debug("Data of size {0} recieved".format(scroll_size))

    while True:
        logger.debug("Scrolling...")

        tweet_text = {}

        # Before scroll, process current batch of hits
        hits = data["hits"]["hits"]
        for hit in hits:
            tweet = hit["_source"]
            tweet_text[tweet['id']] = {"text": tweet["text"], "collection_source": "online"}

        emotion_tweets, no_emotion_tweets = get_emotions(tweet_text)

        for tweet_id, emotions in emotion_tweets.items():
            logger.debug("Loading the emotions of tweet {0} into ElasticSearch".format(tweet_id))
            es.index('emotions', emotions, id=tweet_id)

        data = es.scroll(scroll_id=sid, scroll='2m')

        # Update the scroll ID
        sid = data['_scroll_id']

        # Get the number of results that returned in the last scroll
        scroll_size = len(data['hits']['hits'])

        logger.debug("Data of size {0} received".format(scroll_size))


if __name__ == '__main__':
    extract_tweet_emotions()
