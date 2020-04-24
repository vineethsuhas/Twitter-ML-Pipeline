import os
import sys

if __name__ == "__main__":
    os.environ.setdefault("DJANGO_SETTINGS_MODULE", "emotiClass.settings")
    APP_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), '../'))
    sys.path.append(APP_DIR)
    app_basename = os.path.basename(APP_DIR)
    os.environ.setdefault('DJANGO_SETTINGS_MODULE', app_basename + '.settings')
