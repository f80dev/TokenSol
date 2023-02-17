

from apscheduler.schedulers.background import BackgroundScheduler
from flask import Flask
from flask_cors import CORS

from flaskr.Tools import log
from flaskr.apptools import async_mint, activity_report_sender

from flaskr.dao import DAO
from flaskr.secret import SECRET_JWT_KEY

#voir pour le choix entre flask run ou app.run() https://www.twilio.com/blog/executer-application-flask

def create_app(config=None) -> (Flask,BackgroundScheduler):
  """
  Création des principales instances
  config_name peut prendre les valeurs : ["prod","dev","local"]
  :return:
  """
  r_scheduler = BackgroundScheduler()
  log("Initialisation du scheduler ok")

  _app = Flask(__name__,instance_relative_config=True)
  log("Initialisation de l'app ok")

  if type(config)==dict:
    _app.config.from_mapping(config)
  else:
    if config is None: config="config.devConfig"
    if type(config)==str:
      if not config.endswith("onfig"):config=config+"Config"
      if not config in ["localConfig","testConfig","devConfig","prodConfig","demoConfig"]: config="localConfig"
      _app.config.from_object("config."+config)
    else:
      _app.config.from_object(config)

  from . import api
  _app.register_blueprint(api.bp)

  log("Mise a place du modele CORS")
  CORS(_app)

  return _app,r_scheduler


#domain_server=sys.argv[1]
#debug_mode=("debug" in sys.argv)
#db_server=DBSERVER_SYSTEM if len(sys.argv)<=3 else sys.argv[3]
#activity_report_dest=sys.argv[4] if len(sys.argv)>4 else ""
# config={
#   "DEBUG": debug_mode,                    # some Flask specific configs
#   "CACHE_TYPE": "SimpleCache",      # Flask-Caching related configs
#   "CACHE_DEFAULT_TIMEOUT": 300,
#   "APPLICATION_ROOT":sys.argv[2],
#   "DOMAIN_APPLI":sys.argv[2],
#   "DOMAIN_SERVER":domain_server,
#   "ACTIVITY_REPORT":activity_report_dest,
#   "DB_SERVER":db_server,
#   "DB_NAME":DBNAME_SYSTEM,
#   "UPDLOAD_FOLDER":TEMP_DIR,
#   "JWT_SECRET_KEY":SECRET_JWT_KEY
# }
