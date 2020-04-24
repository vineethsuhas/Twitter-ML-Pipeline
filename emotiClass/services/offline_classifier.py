"""
Historical Data available in the form of files.

This process performs the following operations:

    1. Loads the data into the raw data store
    2. Classifies the emotion for tweets and pushes them to elasticsearch.
"""
import os
import sys
import glob
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

import pandas as pd
from pyspark.sql import functions as F
from pyspark.sql import types as DT

from loader.models import OfflineLoader

from services.utils import _thread_locals
from services.utils import init_spark
from services.online_classifier import process_tweet


nrc_lexicon = None
TWEET_ID_KEY = "temp"
logger = logging.getLogger(settings.EC_LOG)


def get_file_path(project_name):
    file_path = OfflineLoader.objects.get(project_offlineloader__name=project_name).file_path
    return file_path


def get_key_names(project_name):
    mapping = OfflineLoader.objects.get(project_offlineloader__name=project_name).field_mappings
    tweet_text_key = mapping.get('text', 'text')
    tweet_id_key = mapping.get('id', 'id')
    return tweet_id_key, tweet_text_key


def infer_file_schema(project_name):
    file_path = get_file_path(project_name)

    # TODO: Handle when no file exists initially.
    data_file = glob.glob(file_path + "/*.csv")[0]

    SPARK_SESSION = getattr(_thread_locals, 'SPARK_SESSION')
    static_df = SPARK_SESSION\
        .read \
        .format('csv')\
        .option('inferSchema', 'true')\
        .option('header', 'true')\
        .option('multiline', 'true')\
        .option('quote', '"')\
        .option('delimiter', ',')\
        .option('escape', '"')\
        .load(data_file).limit(5)

    static_schema = static_df.schema

    return static_schema


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
def retrieve_emotions(arr):
    return get_emotions(arr)


def write_to_es(doc, prj_name):
    from elasticsearch import Elasticsearch

    es = Elasticsearch()
    doc_dict = doc.asDict()
    emotions = doc_dict.pop('emotions')
    doc_dict.pop('processed')

    raw_data_idx = settings.ES_IDX_OFFLINE_RAW_PREFIX + prj_name
    emotions_idx = settings.ES_IDX_EMOTIONS_PREFIX + prj_name

    es.index(raw_data_idx, doc_dict, id=doc_dict[TWEET_ID_KEY])
    es.index(emotions_idx, emotions, id=emotions['tweet_id'])


def consume_files(project_name):
    file_path = get_file_path(project_name)
    static_schema = infer_file_schema(project_name)

    mapping = OfflineLoader.objects.get(project_offlineloader__name=project_name).field_mappings
    tweet_text_key = mapping.get('text', 'text')
    tweet_id_key = mapping.get('id', 'id')
    setattr(sys.modules['__main__'], 'TWEET_ID_KEY', tweet_id_key)

    SPARK_SESSION = getattr(_thread_locals, 'SPARK_SESSION')
    stream_df = SPARK_SESSION\
        .readStream\
        .schema(static_schema)\
        .format("csv")\
        .option("maxFilesPerTrigger", 1)\
        .option('multiline', 'true')\
        .option("header", "true")\
        .option('quote', '"')\
        .option('delimiter', ',')\
        .option('escape', '"')\
        .load(file_path + "/*.csv")

    # Apply NLTK Processing:
    processed = stream_df \
        .withColumn('processed', process_tweet(stream_df[tweet_text_key]))

    emotions = processed\
        .withColumn('emotions', retrieve_emotions(F.struct(processed[tweet_text_key],
                                                           processed[tweet_id_key],
                                                           processed['processed'])),
    )

    # Write the Data to ElasticSearch using forEach sink
    writer_query = emotions \
        .writeStream \
        .foreach(lambda x: write_to_es(x, project_name)) \
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
                        help='Project for which upload has to be invoked',
                        default=False,
                        required=True)
    parser.add_argument('-d',
                        '--debug',
                        type=str,
                        help='To push only few messages to the test topic: true/false',
                        default=False,
                        required=False)

    args = parser.parse_args()
    project_name = args.project
    debug = True if args.debug == "true" else False
    if debug:
        IS_TEST_ENV = True
        TWITTER_KAFKA_TOPIC = "test_twitter_stream"
        ES_EMOTIONS_INDEX = "test_emotions"

    # Init spark session
    init_spark()

    # Init NRC Lexicon
    # TODO: Broadcasting nrc_lexicon:
    #  https://stackoverflow.com/questions/46486419/global-variables-not-recognized-in-lambda-functions-in-pyspark
    logger.debug("computing the NRC Lexicon...")
    nrc_lexicon = get_nrc_data()

    # Start consuming messages
    consume_files(project_name)
