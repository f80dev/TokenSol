import atexit
import os
import ssl
import sys

from flask_jwt_extended import JWTManager
from flask_socketio import SocketIO

from flaskr import create_app, async_mint, activity_report_sender
from flaskr.Tools import log


if __name__=="__main__":
  app,scheduler=create_app(sys.argv[1] if len(sys.argv)>1 else "localConfig")
  log("Version du serveur : "+app.config["VERSION"])

  socketio = SocketIO(app,cors_allowed_origins="*")
  log("Initialisation de la websocket")

  jwt = JWTManager(app)

  scheduler.add_job(func=async_mint, trigger="interval", seconds=30,max_instances=1,args=(app.config,3,""))
  scheduler.add_job(func=activity_report_sender, trigger="interval", seconds=3600*24,max_instances=1,args=(app.config,"CR nfluent"))
  scheduler.start()
  atexit.register(lambda: scheduler.shutdown())

  domain_server=app.config["DOMAIN_SERVER"]
  index_port=domain_server.rindex(":")
  _port=int(domain_server[index_port+1:])

  app.config.update(SESSION_COOKIE_SECURE=True,SESSION_COOKIE_HTTPONLY=True,SESSION_COOKIE_SAMESITE='Lax')
  debug_mode=app.config["DEBUG"]
  domain_server=app.config["DOMAIN_SERVER"]

  log("Working directory : "+os.getcwd())

  if not "127.0.0.1" in domain_server and not "localhost" in domain_server:
    activity_report_sender(app.config,"Démarage du serveur "+app.config["DOMAIN_SERVER"]+" en mode "+("debug" if debug_mode else "prod"))

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
    app.run(port=_port,host="0.0.0.0")
  #socketio.run(app,port=_port,host="0.0.0.0",debug=debug_mode,allow_unsafe_werkzeug=True,use_reloader=debug_mode)

  if not "127.0.0.1" in domain_server:
    activity_report_sender(app.config,"Arret du server en mode "+("debug" if debug_mode else "prod"))
