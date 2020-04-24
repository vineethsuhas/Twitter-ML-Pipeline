"""
Loading the data from various sources:

    1) File Systems (csv, json, txt)
    2) HDFS
    3) DataBases
"""
import os
import csv
import logging

from django.conf import settings

from services.data_service import DataService


logger = logging.getLogger(settings.EC_LOG)


def create_docs_from_csv(path, nrows=None):
    docs = []
    with open(path, 'r') as f:
        csv_reader = csv.reader(f)
        header = next(csv_reader, None)

        # If file is empty return empty list
        if not header:
            return docs

        # Get each row as a document into the list
        for i, row in enumerate(csv_reader):
            doc = {}
            for idx, val in enumerate(row):
                doc[header[idx]] = val if val else None
            docs.append(doc)

            # Read only nrows of documents.
            if nrows and i == nrows:
                break

    return docs


def load_offline_data():
    data_path = os.path.join(settings.DATA_DIR, 'twitter_data', 'ira_tweets_csv_hashed.csv')
    docs = create_docs_from_csv(data_path, nrows=100)
    writer = DataService(settings.ES_IDX_OFFLINE_RAW_PREFIX)
    status, failures = writer.bulk_write(docs, 'tweetid')
    if not status:
        logger.debug("Failed to write tweets with IDs: {0}".format(failures))
    else:
        logger.debug("Successfully Loaded the data")


if __name__ == '__main__':
    load_offline_data()
