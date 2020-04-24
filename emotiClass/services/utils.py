import os
import logging
from threading import local

from django.conf import settings

import pandas as pd

from nltk import regexp_tokenize
from nltk.stem import PorterStemmer
from nltk.corpus import stopwords
from nltk.stem import WordNetLemmatizer

from pyspark.sql import SparkSession


_thread_locals = local()
logger = logging.getLogger(settings.EC_LOG)


def init_spark(app_name="emotionClassification"):
    """
    This will initialize the spark session
    :param app_name:
    :return: None
    """
    logger.debug("Initializing the Spark Session...")
    SPARK_SESSION = SparkSession\
        .builder\
        .appName(app_name)\
        .getOrCreate()

    # INFO:
    logger.debug("App Name: {0}".format(SPARK_SESSION.sparkContext.appName))
    logger.debug("Python Version: {0}".format(SPARK_SESSION.sparkContext.pythonVer))
    logger.debug("Spark UI: {0}".format(SPARK_SESSION.sparkContext.uiWebUrl))
    logger.debug("Spark User: {0}".format(SPARK_SESSION.sparkContext.sparkUser))

    setattr(_thread_locals, 'SPARK_SESSION', SPARK_SESSION)


def compute_nrc():
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

    global nrc_lexicon
    nrc_lexicon = nrc_data

    return


def pre_process(text):
    final_words = []
    # Tokenizing
    words = regexp_tokenize(text, '\w+')

    # Stop Words removal
    sw_l = stopwords.words('english')
    words_without_stopwords = [word for word in words if word not in sw_l]

    # Stemming and Lemmatizing
    stemmer = PorterStemmer()
    lemmatizer = WordNetLemmatizer()
    for word in words_without_stopwords:
        word = stemmer.stem(word)
        word = lemmatizer.lemmatize(word)
        final_words.append(word)

    # List of final words to classify the emotions
    return final_words
