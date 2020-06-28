"""
Title: Streaming Service
Author: Vineeth Suhas Challagali (vsc5068)
Code Version: v1.0.0
Description:
    Streams the data from the Twitter using Twitter API's and pushes them to Kafka topic.
    The topic name is dynamic based on the project name.
"""

"""
Resouces:
# curl -X PUT "localhost:9200/online_index/_settings?pretty" -H 'Content-Type: application/json' -d'{"index" : {"mapping.total_fields.limit": 2000}}'
/Users/vineethsuhas/vineeth/handsOn/mpsDaan/indepStudy/temp/bin/python /Users/vineethsuhas/vineeth/handsOn/mpsDaan/indepStudy/v1.0.0/streaming_service.py -t="corona,covid19"
"""

import os
import sys
import argparse
import logging

import django

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "emotiClass.settings")
APP_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), '../'))
sys.path.append(APP_DIR)
app_basename = os.path.basename(APP_DIR)
os.environ.setdefault('DJANGO_SETTINGS_MODULE', app_basename + '.settings')
django.setup()


from django.conf import settings

import tweepy
from confluent_kafka import Producer

from loader.models import TwitterTracks


# TODO: set the globals in _thread_locals
TEST_COUNTER = 0
IS_TEST_ENV = False
logger = logging.getLogger(settings.EC_LOG)


def delivery_report(err, msg):
    """ Called once for each message produced to indicate delivery result.
        Triggered by poll() or flush(). """
    if err is not None:
        logger.debug('Message delivery failed: {}'.format(err))
    else:
        logger.debug('Message delivered to {} [{}]'.format(msg.topic(), msg.partition()))


def push_message_using_confluent(topic, message):
    p = Producer({'bootstrap.servers': '127.0.0.1'})
    p.poll(0)

    # Asynchronously produce a message, the delivery report callback
    # will be triggered from poll() above, or flush() below, when the message has
    # been successfully delivered or failed permanently.
    p.produce(topic, message.encode('utf-8'), callback=delivery_report)

    # Wait for any outstanding messages to be delivered and delivery report
    # callbacks to be triggered.
    p.flush()


class MyStreamListener(tweepy.StreamListener):

    def __init__(self):
        auth = tweepy.OAuthHandler(settings.CONSUMER_KEY, settings.CONSUMER_SECRET)
        auth.set_access_token(settings.ACCESS_TOKEN, settings.ACCESS_TOKEN_SECRET)
        api = tweepy.API(auth)
        super(MyStreamListener, self).__init__(api)

    def on_data(self, raw_data):
        global kafka_topic

        logger.debug("Pushing tweet {0} to Kakfa".format(raw_data))
        push_message_using_confluent(kafka_topic, raw_data)
        return

    def on_status(self, status):
        logger.debug(status.text)


class TestListener(MyStreamListener):

    def on_data(self, raw_data):
        global TEST_COUNTER
        if TEST_COUNTER == 10:
            """
            Q. How to stop the streaming?
            A. https://stackoverflow.com/questions/33498975/unable-to-stop-streaming-in-tweepy-after-one-minute
            """
            return False
        super_call = super(TestListener, self).on_data(raw_data)
        TEST_COUNTER += 1
        return super_call


def publish_tweets(tracks):
    global IS_TEST_ENV

    stream_listener = MyStreamListener() if not IS_TEST_ENV else TestListener()
    tweets = tweepy.Stream(auth=stream_listener.api.auth, listener=stream_listener)
    tweets.filter(track=tracks)


if __name__ == '__main__':
    parser = argparse.ArgumentParser()

    parser.add_argument('-p',
                        '--project',
                        type=str,
                        help='Project for which streaming has to be invoked',
                        required=True)

    parser.add_argument('-t',
                        '--tracks',
                        type=str,
                        help='Filters based on which tweets has to be fetched (Comma Separated)',
                        required=False)

    parser.add_argument('-d',
                        '--debug',
                        type=str,
                        help='To push only few messages to the test topic: true/false',
                        default=False,
                        required=False)

    # Get the arguments
    args = parser.parse_args()
    project = args.project
    tracks = args.tracks.split(',') if args.tracks else ""

    debug = True if args.debug == "true" else False
    if debug:
        IS_TEST_ENV = True
        TWITTER_KAFKA_TOPIC = "test_twitter_stream"
        kafka_topic = "test_twitter_stream"
    else:
        kafka_topic = settings.TWITTER_KAFKA_TOPIC_PREFIX + project

    if project:
        prj_tracks = TwitterTracks.objects.get(project_twittertracks__name=project).search_terms
        tracks += prj_tracks

    publish_tweets(tracks)
