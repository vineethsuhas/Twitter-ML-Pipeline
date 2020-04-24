import os
import sys
import json
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

from confluent_kafka import Consumer

from services.data_service import DataService


logger = logging.getLogger(settings.EC_LOG)


def load_raw_online_data(message, project):
    es_idx = settings.ES_IDX_ONLINE_RAW_PREFIX + project
    writer = DataService(es_idx)
    json_message = json.loads(message)

    if "id" not in json_message:
        return

    status = writer.write(json_message, 'id')
    if not status:
        logger.debug("Failed to write tweet with ID: {0}".format(json_message['id']))
    else:
        logger.debug("Successfully written online tweet with ID: {0}".format(json_message['id']))


def poll_message_using_confluent(project):
    c = Consumer({
        'bootstrap.servers': 'localhost:9092',
        'group.id': 'twitter-stream-consumer-group',
        'auto.offset.reset': 'earliest'
    })

    topic = settings.TWITTER_KAFKA_TOPIC_PREFIX + project
    c.subscribe([topic])
    logger.debug("Subscribed to the topic {0}".format(topic))

    while True:
        logger.debug("polling for the new messages...")
        msg = c.poll(1)

        if msg is None:
            continue
        if msg.error():
            logger.debug("Consumer error: {}".format(msg.error()))
            continue

        decoded_msg = msg.value().decode('utf-8')
        logger.debug('Received message: {}'.format(decoded_msg))
        load_raw_online_data(decoded_msg, project)

    c.close()


if __name__ == '__main__':
    parser = argparse.ArgumentParser()

    parser.add_argument('-p',
                        '--project',
                        type=str,
                        help='Project for which streaming has to be invoked',
                        required=True)
    # Get the arguments
    args = parser.parse_args()
    project = args.project
    poll_message_using_confluent(project)
