FROM ubuntu:16.04

RUN apt-get clean && apt-get update && apt-get install -y --no-install-recommends binutils \
    build-essential \
    curl \
    less \
    net-tools \
    netcat \
    python-gdal \
    python3-dev \
    software-properties-common \
    unzip \
    wget \
    telnet \


WORKDIR /emotion_classification
RUN mkdir Twitter-ML-Pipeline
COPY . /emotion_classification/Twitter-ML-Pipeline/

RUN /usr/bin/python3 -m venv --without-pip /emotion_classification/ec_venv \
    && curl https://bootstrap.pypa.io/get-pip.py -o /emotion_classification/ec_venv/get-pip.py \
    && /emotion_classification/ec_venv/bin/python3 /emotion_classification/ec_venv/get-pip.py \
    && /emotion_classification/ec_venv/bin/pip install -r /emotion_classification/Twitter-ML-Pipeline/emotiClass/emotiClass/requirements.txt

EXPOSE 8080
CMD [ "/emotion_classification/ec_venv/bin/python", \
      "/emotion_classification/Twitter-ML-Pipeline/emotiClass/manage.py", \
      "runserver",  \
      "0.0.0.0:8080" ]