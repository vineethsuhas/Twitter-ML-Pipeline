## `Data Pipeline`

### `SETUP GUIDE`

#### `Creating a virtual environment and cloning the project`

* Clone the Repository:
~~~~
# Change directory to your preferred location
cd </User/project/location/>

# Clone the repository to some location </User/project/location/>
git clone git@gitlab.com:geethapriya/twitter-ml-pipeline.git
~~~~

* Setup Virtual Environment:
~~~~
# Verify if the python version. 
# Recommended Python Version - 3.6 
python --version

# Change the working directory to your project location
cd </User/project/location/>

# Create venv:
python -m venv ec_venv

# Activate venv:
source ec_venv/bin/activate

# Install all the requirements
pip install -r twitter-ml-pipeline/emotiClass/emotiClass/requirements.txt
~~~~

* Run the following sequence of commands to verify the setup.
~~~~
cd twitter-ml-pipeline/emotiClass

python manage.py check
~~~~

#### `Configure Private Settings`
* Create local_settings.py file in emotiClass/emotiClass/config/ folder
* Add your Twitter credential keys to the file:
~~~~
CONSUMER_KEY = "\<YOUR CONSUMER KEY\>" 
CONSUMER_SECRET = "\<YOUR CONSUMER SECRET KEY\>"
ACCESS_TOKEN = "\<YOUR ACCESS TOKEN\>"
ACCESS_TOKEN_SECRET = "\<YOUR ACCESS TOKEN SECRET\>"
~~~~

#### `TOOLS`

* Follow the installation guides of following tools and services:

| Tool | URL |
| --- | --- |
| Kafka | https://kafka.apache.org/quickstart |
| Elasticsearch | https://www.elastic.co/guide/en/elasticsearch/reference/current/install-elasticsearch.html |
| Kibana | https://www.elastic.co/guide/en/kibana/6.8/install.html |

* NOTE: 
    * Kafka requires zookeeper to be up and running. The above URL mentions to run both of them together.
    * To monitor Elasticsearch indexes locally. Install a chrome plugin **_Elasticsearch Head_**


#### `MEDIA`

* The media folder in the project directory handles the data storage and uploads. Below table gives a brief description of each sub-folder in media.
    
| Folder | Usage |
| --- | --- | 
| data/ | Consists of sample data files required for the project setup. |
| uploads/ | Consists of uploaded sample uploads. |
| nrc_lexicons/ | NRC Lexicon used for emotion classification. |
| db.sqlite3 | The database for admin configurations. |
