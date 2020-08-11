"""
Loading the data from various sources:

    1) File Systems (csv, json, txt)
    2) HDFS
    3) DataBases
"""
import os
import sys
import logging
import argparse

import django

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "emotiClass.settings")
APP_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), '../'))
sys.path.append(APP_DIR)
app_basename = os.path.basename(APP_DIR)
os.environ.setdefault('DJANGO_SETTINGS_MODULE', app_basename + '.settings')
django.setup()

from django.conf import settings

from loader.models import OfflineLoader

from services.utils import _thread_locals
from services.utils import init_spark
from services.offline_classifier import infer_file_schema


logger = logging.getLogger(settings.EC_LOG)


def get_file_path(project_name):
    file_path = OfflineLoader.objects.get(project_offlineloader__name=project_name).file_path
    return file_path


def write_to_es(doc, prj_name):
    from elasticsearch import Elasticsearch

    es = Elasticsearch()
    doc_dict = doc.asDict()

    es_idx = settings.ES_IDX_TOPIC_EMOTIONS + prj_name
    es.index(es_idx, doc_dict, id=doc_dict["X"])


def consume_files(project_name):
    file_path = get_file_path(project_name)
    static_schema = infer_file_schema(project_name)

    mapping = OfflineLoader.objects.get(project_offlineloader__name=project_name).field_mappings
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

    # Write the Data to ElasticSearch using forEach sink
    writer_query = stream_df \
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

    args = parser.parse_args()
    project_name = args.project

    # Init spark session
    init_spark()

    # Start consuming messages
    consume_files(project_name)
