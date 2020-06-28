"""
Title: Online Classifier
Author: Vineeth Suhas Challagali (vsc5068)
Code Version: v1.0.0
Description:
    A spark application which connects to the Kafka topic and classifies the emotions of the text of each message.
    The emotions are loaded into the Elasticsearch emotions index.
"""

import os
import sys
import glob
import json
import argparse
import logging

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "emotiClass.settings")
APP_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), '../'))
sys.path.append(APP_DIR)
app_basename = os.path.basename(APP_DIR)
os.environ.setdefault('DJANGO_SETTINGS_MODULE', app_basename + '.settings')

from django.conf import settings

import pandas as pd
from pyspark.sql import SparkSession
import pyspark.sql.functions as F
import pyspark.sql.types as DT

from services.utils import pre_process


# GLOBALS:
# Initializing the global variable to store spark session:
# TODO: Move this to _thread_locals
spark_session = None
nrc_lexicon = None
ES_EMOTIONS_INDEX = "emotions"
IS_TEST_ENV = False
logger = logging.getLogger(settings.EC_LOG)


def init_conf():
    """
    Initializing any configurations required before starting the spark session.
    :return: None
    """
    logger.debug("Initializing the configuration...")

    os.environ["PYSPARK_SUBMIT_ARGS"] = """
        --packages org.apache.spark:spark-sql-kafka-0-10_2.11:2.4.4 pyspark-shell
    """
    return


def init_spark(app_name="emotiApp"):
    """
    This will initialize the spark session
    :param app_name:
    :return: None
    """
    logger.debug("Initializing the Spark Session...")
    global spark_session

    spark_session = SparkSession\
        .builder\
        .appName(app_name)\
        .getOrCreate()

    # INFO:
    logger.debug("App Name: {0}".format(spark_session.sparkContext.appName))
    logger.debug("Python Version: {0}".format(spark_session.sparkContext.pythonVer))
    logger.debug("Spark UI: {0}".format(spark_session.sparkContext.uiWebUrl))
    logger.debug("Spark User: {0}".format(spark_session.sparkContext.sparkUser))


def infer_schema(schema_path):
    """
    This is to infer the schema before starting the streaming.
    :param schema_path: String
    :return: dict
    """
    logger.debug("Started to Infer the schema of Kafka Stream")

    if not os.path.exists(schema_path):
        logger.debug("Found an existing schema in the given location; Using it to infer Schema")

        # Get the small batch from the kafka:
        smallBatch = spark_session.read\
            .format("kafka")\
            .option("kafka.bootstrap.servers", "127.0.0.1:9092")\
            .option("subscribe", "twitter_stream")\
            .option("startingOffsets", "earliest")\
            .option("endingOffsets", """{"twitter_stream":{"0":2}}""")\
            .load()\
            .selectExpr("CAST(value AS STRING) as STRING")

        # Write it to the local storage:
        smallBatch.write\
            .format('text')\
            .save(schema_path)

    # Read the text file as json from which schema can be inferred:
    schema_file = glob.glob(schema_path + "/*.txt")[0]
    schema = spark_session.read.json(schema_file).schema
    logger.debug("Successfully retrieved the schema of Kafka Stream.")
    return schema


def get_nrc_data():
    """
    Compute the NRC lexicon and store in global memory
    :return:
    """
    nrc_path = os.path.join(settings.NRC_LEXICON_DIR,
                            "NRC-Emotion-Lexicon-v0.92",
                            "NRC-Emotion-Lexicon-Wordlevel-v0.92.txt")
    nrc_data = pd.read_csv(nrc_path, names=["word", "emotion", "association"], sep="\t", header=None)
    nrc_data = nrc_data[~nrc_data.word.isna()]
    nrc_data = nrc_data.pivot(index='word', columns='emotion', values='association')
    nrc_data.columns.name = None
    return nrc_data


def get_emotions(arr):
    """

    :param arr:
    :return:
    """
    (tweet_text, tweet_id, processed_tweet) = arr

    total_em = None
    for word in processed_tweet:
        try:
            em = nrc_lexicon.loc[word, :]
        except KeyError:
            # logger.debug("{0} DoesNotExist in NRC-Lexicon".format(word))
            continue
        total_em = total_em + em if isinstance(total_em, pd.Series) else em

    if isinstance(total_em, pd.Series):
        final_dict = total_em.to_dict()
        final_dict.update({'tweet_text': tweet_text, 'tweet_id': tweet_id})
        return final_dict

    # Return null emotions
    null_emotions = {emotion: 0 for emotion in nrc_lexicon.columns}
    null_emotions.update({'tweet_text': tweet_text, 'tweet_id': tweet_id})
    return null_emotions


@F.udf(DT.MapType(DT.StringType(), DT.StringType()))
def json_parse_message(message):
    return json.loads(message)


# TODO: Try to implement this
# @F.udf(DT.StringType())
# def filter_keys(*args):
#     (json_message, key) = args
#     return json_message.get("text", "")


@F.udf(DT.StringType())
def filter_tweet_text(message):
    return message.get("text", "")


@F.udf(DT.StringType())
def filter_tweet_id(message):
    return message.get("id", "0")


@F.udf(DT.ArrayType(DT.StringType()))
def process_tweet(tweet_text):
    return pre_process(tweet_text)


@F.udf(DT.MapType(DT.StringType(), DT.StringType()))
def retrieve_emotions(arr):
    return get_emotions(arr)


def write_to_es(doc, prj_name):
    from elasticsearch import Elasticsearch

    es = Elasticsearch()

    emotions_idx = settings.ES_IDX_EMOTIONS_PREFIX + prj_name
    es.index(emotions_idx, doc, id=doc['tweet_id'])


def consume(project, schema_path=""):
    """
    **
    Structured Streaming Prg Guide:
    https://spark.apache.org/docs/latest/structured-streaming-programming-guide.html#using-foreach-and-foreachbatch
    **

    Spark consumer to process messages from kafka
    :param project: String
    :param schema_path: String
    :return:
    """

    # Retrieve the schema
    if schema_path:
        logger.debug("Opted to infer the schema of Kafka Stream")
        schema = infer_schema(schema_path)

    logger.debug("Initiating the Spark Streaming...")
    global spark_session

    kafka_topic = settings.TWITTER_KAFKA_TOPIC_PREFIX + project

    # Load the data in the form of JSON:
    kafka_stream = spark_session\
        .readStream\
        .format("kafka")\
        .option("kafka.bootstrap.servers", "localhost:9092")\
        .option("subscribe", kafka_topic)\
        .option("startingOffsets", "earliest")\
        .load()\
        .selectExpr("CAST(value AS STRING) as MESSAGE")

    # Parse the Kafka message into JSON:
    json_message = kafka_stream\
        .withColumn('json_message', json_parse_message(kafka_stream['MESSAGE']))\
        .select('json_message')

    # Retrieve Tweet Text and ID:
    tweets = json_message\
        .withColumn('tweet_text', filter_tweet_text('json_message'))

    tweets = tweets\
        .withColumn('tweet_id', filter_tweet_id('json_message'))\
        .select(['tweet_id', 'tweet_text'])

    # Apply NLTK Processing:
    processed = tweets\
        .withColumn('processed', process_tweet(tweets['tweet_text']))

    emotions = processed\
        .withColumn('emotions', retrieve_emotions(F.struct(processed['tweet_text'],
                                                           processed['tweet_id'],
                                                           processed['processed'])))\
        .select('emotions')

    # Write the Data to ElasticSearch using forEach sink
    writer_query = emotions\
        .writeStream\
        .foreach(lambda x: write_to_es(x['emotions'], project))\
        .start()

    # Write the query ID to console for reference.
    logger.debug("Writer Query Invoked with ID: {0}".format(writer_query.id))

    # Await for completion
    writer_query.awaitTermination()


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('-p',
                        '--project',
                        type=str,
                        help='Project for which classification to be invoked',
                        default=False,
                        required=False)

    parser.add_argument('-d',
                        '--debug',
                        type=str,
                        help='To push only few messages to the test topic: true/false',
                        default=False,
                        required=False)


    args = parser.parse_args()
    project = args.project
    debug = True if args.debug == "true" else False
    if debug:
        IS_TEST_ENV = True
        TWITTER_KAFKA_TOPIC = "test_twitter_stream"
        ES_EMOTIONS_INDEX = "test_emotions"

    # Location where the schema of the twitter JSON is stored:
    TWITTER_SCHEMA_LOCATION = settings.OFFLINE_SCHEMA_PATH

    # Init configuration
    init_conf()

    # Init spark session
    init_spark()

    # Init NRC Lexicon
    logger.debug("Loading the NRC Lexicon...")
    nrc_lexicon = get_nrc_data()

    # Start consuming messages
    consume(project)
