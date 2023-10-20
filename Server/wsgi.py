import atexit
import os
import ssl
import sys

from flask_jwt_extended import JWTManager
from flask_socketio import SocketIO

from flaskr import create_app
from flaskr.Mintpool import Mintpool
from flaskr.Tools import log, send, register_fonts
from flaskr.apptools import activity_report_sender

def receive(app):
  send(app,"refresh")
  log("Réception de disconnect")


if __name__=="__main__":
  app,scheduler=create_app(sys.argv[1] if len(sys.argv)>1 else "akashConfig")
  mintpool=Mintpool(app.config)
  log("Version du serveur : "+app.config["VERSION"])

  socketio = SocketIO(app,cors_allowed_origins="*",logger=True,engineio_logger=True,manage_session=True)
  app.config["socket"]=socketio
  socketio.on_event("disconnect",receive(app))
  log("Initialisation de la websocket")

  jwt = JWTManager(app)

  scheduler.add_job(func=mintpool.async_mint, trigger="interval", seconds=30,max_instances=1,args=(3,""))
  scheduler.add_job(func=activity_report_sender, trigger="interval", seconds=3600*24,max_instances=1,args=(app.config,"CR nfluent"))
  scheduler.start()
  log("Scheduler started")
  atexit.register(lambda: scheduler.shutdown())

  # domain_server=app.config["DOMAIN_SERVER"]
  # index_port=domain_server.rindex(":")
  # _port=int(domain_server[index_port+1:])
  # log("Domain server "+domain_server+":"+str(_port))
  _port=4242

  app.config.update(SESSION_COOKIE_SECURE=True,SESSION_COOKIE_HTTPONLY=True,SESSION_COOKIE_SAMESITE='Lax')
  debug_mode=app.config["DEBUG"]
  domain_server=app.config["DOMAIN_SERVER"]

  register_fonts(limit=1000 if not debug_mode else 30)
  log("Working directory : "+os.getcwd())

  if not "127.0.0.1" in domain_server and not "localhost" in domain_server:
    activity_report_sender(app.config,"Démarage du serveur "+app.config["DOMAIN_SERVER"]+"/api/infos en mode "+("debug" if debug_mode else "prod"))

  if "ssl" in sys.argv:
    log("Activation du SSL")
    context = ssl.SSLContext(ssl.PROTOCOL_TLSv1_2)
    try:
      context.load_cert_chain("/certs/fullchain.pem", "/certs/privkey.pem")
      log("Démarage du serveur en mode sécurisé")

      socketio.run(app,debug=debug_mode,port=_port,ssl_context=context,host="0.0.0.0",allow_unsafe_werkzeug=True)
    except:
      log("Le répertoire /root/certs doit contenir les certificats sous forme de fichier fullchain.pem et privkey.pem")
    log("Fonctionnement en mode SSL activé.")
  else:
    log("Pas d'activation du SSL")
    host=domain_server.split("//")[1].split(":")[0]
    log("Démarage des sockets sur port "+str(_port))
    socketio.run(app,port=_port,host="0.0.0.0",debug=debug_mode,allow_unsafe_werkzeug=True,use_reloader=False)
    log("Sockets démarrées")

  if not "127.0.0.1" in domain_server:
    activity_report_sender(app.config,"Arret du server en mode "+("debug" if debug_mode else "prod"))