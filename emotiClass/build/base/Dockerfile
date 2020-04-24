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
    unzip

WORKDIR /emotion_classification
RUN mkdir emotiClass
COPY . /emotion_classification/emotiClass/

CMD [ "/bin/bash" ]

RUN /usr/bin/python3 -m venv --without-pip /emotion_classification/ec_venv \
    && curl https://bootstrap.pypa.io/get-pip.py -o /emotion_classification/ec_venv/get-pip.py \
    && /emotion_classification/ec_venv/bin/python3 /emotion_classification/ec_venv/get-pip.py
#    && /emotion_classification/ec_venv/bin/pip install --no-binary django -r emotiClass/emotiClass/requirements.txt

COPY 

EXPOSE 8080
CMD [ "ec_venv/bin/python", "emotiClass/manage.py", "runserver",  "8080" ]