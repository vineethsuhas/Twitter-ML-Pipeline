import os
import sys
import multiprocessing


BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
ROOT_DIR = os.path.abspath(os.path.join(BASE_DIR, '..'))
LOGS_DIR = os.path.abspath(os.path.join(BASE_DIR, '../logs'))
sys.path.append(BASE_DIR)
sys.path.append(ROOT_DIR)

port_number = 8080
prefix = "emotiClass"
USE_UNIX_SOCKETS = False

if USE_UNIX_SOCKETS:
    bind = "unix:/tmp/%ssock.sock" % prefix
else:
    bind = ":%d" % port_number

proc_name = '%sgunicorn' % prefix
pidfile = '/tmp/%sgunicorn.pid' % prefix

accesslog = os.path.abspath(os.path.join(LOGS_DIR, 'gunicorn-access.log'))
errorlog = os.path.abspath(os.path.join(LOGS_DIR, 'gunicorn-error.log'))

workers = (multiprocessing.cpu_count() * 2) + 1
backlog = 2048
worker_class = "sync"

del prefix

daemon = False
access_log_format = '%({X-Forwarded-For}i)s %(l)s %(u)s %(t)s \"%(r)s\" %(s)s %(b)s \"%({Referer}i)s\" \"%({User-Agent}i)s\" \"%({Cookie}i)s\" %(T)s/%(D)s'
timeout = 240
graceful_timeout = 30
keepalive = 5
preload_app = False
loglevel = "debug"
name = 'gunicorn_django'
