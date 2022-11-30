import atexit
import ssl
import sys

from apscheduler.schedulers.background import BackgroundScheduler
from flask import Flask
from flask_cors import CORS
from flask_jwt_extended import JWTManager
from flask_socketio import SocketIO

from flaskr import api
from flaskr.Tools import log
from flaskr.apptools import async_mint, activity_report_sender

from flaskr.dao import DAO
from flaskr.secret import SECRET_JWT_KEY
from flaskr.settings import DBSERVER_SYSTEM, DBNAME_SYSTEM, TEMP_DIR


def create_app(test_config=None) -> (Flask,BackgroundScheduler):
  """
  Création des principales instances
  :return:
  """
  r_scheduler = BackgroundScheduler()
  log("Initialisation du scheduler ok")

  _app = Flask(__name__)
  log("Initialisation de l'app ok")
  if test_config is None:
    _app.config.from_pyfile("config.py",silent=True)
  else:
    _app.config.from_mapping(test_config)

  _app.register_blueprint(api.bp)

  return _app,r_scheduler


if __name__ == '__main__':
  log("Lecture des paramètres de la ligne de commande")
  domain_server=sys.argv[1]
  debug_mode=("debug" in sys.argv)
  db_server=DBSERVER_SYSTEM if len(sys.argv)<=3 else sys.argv[3]
  activity_report_dest=sys.argv[4] if len(sys.argv)>4 else ""
  config={
    "DEBUG": debug_mode,                    # some Flask specific configs
    "CACHE_TYPE": "SimpleCache",      # Flask-Caching related configs
    "CACHE_DEFAULT_TIMEOUT": 300,
    "APPLICATION_ROOT":sys.argv[2],
    "DOMAIN_APPLI":sys.argv[2],
    "DOMAIN_SERVER":domain_server,
    "ACTIVITY_REPORT":activity_report_dest,
    "DB_SERVER":db_server,
    "DB_NAME":DBNAME_SYSTEM,
    "UPDLOAD_FOLDER":TEMP_DIR,
    "JWT_SECRET_KEY":SECRET_JWT_KEY
  }
  app,scheduler=create_app(config)

  socketio = SocketIO(app,cors_allowed_origins="*")
  log("Initialisation de la websocket")

  log("Mise a place du modele CORS")
  CORS(app)

  jwt = JWTManager(app)

  #scheduler.add_job(func=async_mint, trigger="interval", seconds=30,max_instances=1)
  #scheduler.add_job(func=activity_report_sender, trigger="interval", seconds=3600*24,max_instances=1)
  #scheduler.start()
  #atexit.register(lambda: scheduler.shutdown())

  _port=int(app.config["DOMAIN_SERVER"][app.config["DOMAIN_SERVER"].rindex(":")+1:])

  app.config.update(SESSION_COOKIE_SECURE=True,SESSION_COOKIE_HTTPONLY=True,SESSION_COOKIE_SAMESITE='Lax')

  if not "127.0.0.1" in domain_server:
    activity_report_sender(app,activity_report_dest,"Démarage du serveur "+app.config["DOMAIN_SERVER"]+" en mode "+("debug" if debug_mode else "prod"))

  if "ssl" in sys.argv:
    context = ssl.SSLContext(ssl.PROTOCOL_TLSv1_2)
    try:
      context.load_cert_chain("/certs/fullchain.pem", "/certs/privkey.pem")
      log("Démarage du serveur en mode sécurisé")

      socketio.run(app,debug=debug_mode,port=_port,ssl_context=context,host="0.0.0.0",allow_unsafe_werkzeug=True,use_reloader=debug_mode)
    except:
      log("Le répertoire /root/certs doit contenir les certificats sous forme de fichier fullchain.pem et privkey.pem")
    log("Fonctionnement en mode SSL activé")
  else:
    socketio.run(app,port=_port,host="0.0.0.0",debug=debug_mode,allow_unsafe_werkzeug=True,use_reloader=debug_mode)

  if not "127.0.0.1" in domain_server:
    activity_report_sender(app,activity_report_dest,"Arret du server en mode "+("debug" if debug_mode else "prod"))
