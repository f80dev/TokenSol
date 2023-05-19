#voir https://hackersandslackers.com/configure-flask-applications/
import sys
from os import environ, path
from flaskr.secret import MONGO_WEB3_CONNECTION_STRING, MONGO_SERVER_CONNECTION_STRING, MONGO_INITDB_ROOT_PASSWORD
from flaskr.settings import STATIC_RESSOURCES_DIR

basedir = path.abspath(path.dirname(__file__))


class Config:
  """
  Configuration de base applicable à toutes les versions
  cette configuration peut être surchargé
  """
  SECRET_KEY = environ.get('SECRET_KEY')
  MENU="creator,collection,keys,mint,build,analytics,pool,rescue,logout,admin,faqs,about,help"
  SESSION_COOKIE_NAME = environ.get('SESSION_COOKIE_NAME')
  STATIC_FOLDER = STATIC_RESSOURCES_DIR
  CACHE_TYPE="SimpleCache"
  UPLOAD_FOLDER="./temp/"
  APP_NAME="TokenForge"
  DOMAIN_WALLET="https://wallet.nfluent.io/"
  APP_VERSION="1.0.0"
  CACHE_DEFAULT_TIMEOUT=300
  DEFAULT_PERMISSIONS=["mint","create","build","keys"]
  ACTIVITY_REPORT="paul.dudule@gmail.com"
  DB_NAME="nfluent"
  DB_SERVER = MONGO_SERVER_CONNECTION_STRING
  DB_SERVER_PUBLIC=DB_SERVER.replace(MONGO_INITDB_ROOT_PASSWORD,"*****")
  VERSION="0.2"
  PLATFORMS=[
    {"label":"NFT storage","value":"nftstorage"},
    {"label":"IPFS","value":"ipfs"},
    {"label":"Infura (IPFS)","value":"infura"},
    {"label":"nFluent Server","value":"nfluent"},
    {"label":"nFluent Local Server","value":"nfluent_local"},
    {"label":"Github","value":"github-nfluentdev-storage-main"},
    {"label":"Base NFluent","value":"db-server-nfluent"}
  ]
  NETWORKS=[
    "elrond-devnet",
    "elrond-mainnet",
    "polygon-mainnet",
    "polygon-devnet",
    "solana-devnet",
    "solana-mainnet"
  ]


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
  DOMAIN_SERVER="http://192.168.1.62:4242"          #address du serveur ou s'execute flask



class localConfig(Config):
  """
  configuration local
  """
  FLASK_ENV = 'development'
  DEBUG = True
  TESTING = True
  DB_NAME="nfluent"
  DOMAIN_APPLI="http://localhost:4200"
  DOMAIN_SERVER="http://127.0.0.1:4242"          #address du serveur ou s'execute flask


class akashConfig(prodConfig):
  """
  configuration local
  """
  TESTING = True
  DOMAIN_SERVER="http://provider.bdl.computer:30802"          #address du serveur ou s'execute flask


class testConfig(localConfig):
  TESTING = True
  DB_NAME="nfluent_test"


class demoConfig(localConfig):
  """
  Configuration de démonstration de l'outil de création de NFT
  """
  MENU="creator,faqs,about,help"
  APP_NAME="Token Forge (Démo)"
  APP_VERSION="0.0.1"
  DEFAULT_PERMISSIONS=["mint","create"]
  NETWORKS=[
    "elrond-devnet",
    "polygon-devnet"
  ]
  PLATFORMS=[
    {"label":"nFluent Server","value":"nfluent"},
    {"label":"nFluent Local Server","value":"nfluent_local"}
  ]
