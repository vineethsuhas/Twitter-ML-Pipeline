"""
A service which helps in connecting to the data stores:

v1.0.0 => Uses ElasticSearch as the data store.
"""
import logging

from django.conf import settings

from elasticsearch import Elasticsearch

logger = logging.getLogger(settings.EC_LOG)


class DataService:

    def __init__(self, index):
        self.client = Elasticsearch()
        self.index = index

    @staticmethod
    def get_base_query():
        query = {
           "query": {
              "bool": {
                 "must":[],
                 "must_not": [],
                 "should": []
              }
           },
           "from": 0,
           "size": 10,
           "sort": [],
           "aggs": {}
        }
        return query

    def write(self, doc, id_field):
        try:
            logger.debug("Writing the document with ID: {0}".format(doc[id_field]))
            self.client.create(self.index, doc[id_field], doc)
        except Exception as e:
            logger.debug("Exception while writing: {0}".format(str(e)))
            return False
        return True

    def bulk_write(self, docs, id_field):
        failed_docs = []
        for doc in docs:
            doc_id = doc[id_field]
            try:
                logger.debug("Writing the document with ID: {0}".format(doc_id))
                self.client.create(self.index, doc_id, doc)
            except Exception as e:
                failed_docs.append(doc_id)
        if failed_docs:
            return False, failed_docs
        return True, failed_docs
