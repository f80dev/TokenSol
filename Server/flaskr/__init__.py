

from apscheduler.schedulers.background import BackgroundScheduler
from flask import Flask
from flask_cors import CORS

from flaskr.Tools import log

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
    log("Utilisation de la configuration "+str(config))
    _app.config.from_mapping(config)
  else:
    if config is None: config="config.devConfig"
    if type(config)==str:
      if not config.endswith("onfig"):config=config+"Config"
      if not config in ["localConfig","testConfig","devConfig","prodConfig","demoConfig","akashConfig"]: config="localConfig"
      log("Utilisation de la configuration "+config)
      _app.config.from_object("config."+config)
    else:
      _app.config.from_object(config)

  from . import api
  _app.register_blueprint(api.bp)

  log("Mise a place du modele CORS")
  CORS(_app)

  return _app,r_scheduler

