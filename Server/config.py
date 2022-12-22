#voir https://hackersandslackers.com/configure-flask-applications/
import sys
from os import environ, path
from flaskr.settings import STATIC_FOLDER

from flaskr import TEMP_DIR
from flaskr.secret import MONGO_WEB3_CONNECTION_STRING

basedir = path.abspath(path.dirname(__file__))


class Config:
  """
  Configuration de base applicable à toutes les versions
  """
  SECRET_KEY = environ.get('SECRET_KEY')
  SESSION_COOKIE_NAME = environ.get('SESSION_COOKIE_NAME')
  STATIC_FOLDER = STATIC_FOLDER
  CACHE_TYPE="SimpleCache"
  UPLOAD_FOLDER=TEMP_DIR
  CACHE_DEFAULT_TIMEOUT=300
  ACTIVITY_REPORT="paul.dudule@gmail.com"
  DB_SERVER = MONGO_WEB3_CONNECTION_STRING


class prodConfig(Config):
  """
  Configuration de production destinée aux utilisateurs finaux
  """
  FLASK_ENV = 'production'
  DEBUG = False
  TESTING = False
  DB_NAME="nfluent"
  DOMAIN_APPLI="https://tokenforge.nfluent.io"
  DOMAIN_SERVER="https://api.nfluent.io:4242"          #address du serveur ou s'execute flask


class devConfig(Config):
  """
  configuration de dev en ligne
  """
  FLASK_ENV = 'development'
  DEBUG = True
  TESTING = False
  DB_NAME="nfluent_dev"
  DOMAIN_APPLI="https://tokenfactory.nfluent.io"
  DOMAIN_SERVER="https://server.f80lab.com:4242"          #address du serveur ou s'execute flask



class localConfig(Config):
  """
  configuration local
  """
  FLASK_ENV = 'development'
  DEBUG = True
  TESTING = True
  DB_NAME="nfluent_local"
  DOMAIN_APPLI="http://localhost:4200"
  DOMAIN_SERVER="http://127.0.0.1:4242"          #address du serveur ou s'execute flask


