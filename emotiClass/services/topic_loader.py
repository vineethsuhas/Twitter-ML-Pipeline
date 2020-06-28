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

from tqdm import tqdm
import pandas as pd
from django.conf import settings

import elasticsearch


logger = logging.getLogger(settings.EC_LOG)


def get_file_path(existing_path=None):
    if existing_path:
        path = existing_path
    else:
        path = os.path.join(settings.MEDIA_DIR, 'data', 'topic_modeled_tweets', 'tweets_with_topics.csv')

    logger.info("The path of the file is %s".format(path))
    return path


def load_offline_data(path):
    data_path = get_file_path(path)

    emotions = pd.read_csv(data_path, index_col=0)

    es = elasticsearch.Elasticsearch()

    # Load the data into the Elasticsearch
    for i, row in tqdm(enumerate(emotions.iterrows())):
        # for i, row in enumerate(dat.iterrows()):
        row_dict = row[1].to_dict()
        es.index("topic_modeled_emotions_new", row_dict, id=row_dict['X'])


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('-p',
                        '--path',
                        type=str,
                        help='Path to load the data from',
                        default=False,
                        required=False)
    import ipdb; ipdb.set_trace()
    args = parser.parse_args()
    path = args.path
    load_offline_data(path)
