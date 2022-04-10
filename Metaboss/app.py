import os
import platform
import ssl
import subprocess
import sys

from flask import Response, request, jsonify, send_file, Flask
from flask_cors import CORS

from Metaboss.ipfs import IPFS

app = Flask(__name__)

#voir la documentation de metaboss:


def exec(command:str,param:str="",account:str=""):
  progname="metaboss-ubuntu-latest" if platform.system()!="Windows" else "metaboss.exe"
  cmd=progname+" "+command+" "+param+" --keypair admin.json "
  if len(account)>0:cmd=cmd+" --account "+account

  mes=subprocess.run(cmd,capture_output=True,timeout=2000,shell=True)
  print("Execution de "+cmd+" retourne "+str(mes.stderr,"ansi"))

  return {"error":str(mes.stderr,"ansi")}


#http://127.0.0.1:9999/api/update/?account=GwCtQjSZj3CSNRbHVVJ7MqJHcMBGJJ9eHSyxL9X1yAXy&url=
#TODO: ajouter les restrictions d'appel
@app.route('/api/update/')
#https://metaboss.rs/set.html
def update():
  url=request.args.get("url")
  account=request.args.get("account")
  return exec("update","uri --new-uri "+url,account=account)

@app.route('/api/keys/',methods=["POST","GET"])
#https://metaboss.rs/set.html
def keys():
  if request.method=="GET":
    return jsonify({"files":os.listdir("./*.json")})
  else:
    obj=request.json()
    f = open(obj["name"], "w")
    f.write(obj.key)
    f.close()
    return jsonify({"message":"ok"})


@app.route('/api/update_obj/',methods=["POST"])
def update_obj():
  ipfs=IPFS("/ip4/161.97.75.165/tcp/5001/http",5001)
  url=ipfs.get_link(ipfs.add(request.json))
  account=request.args.get("account")
  return exec("update","uri --new-uri "+url,account=account)



#voir https://metaboss.rs/burn.html
#http://127.0.0.1:9999/api/burn/?account=GwCtQjSZj3CSNRbHVVJ7MqJHcMBGJJ9eHSyxL9X1yAXy&url=
#TODO: ajouter les restrictions d'appel
@app.route('/api/burn/')
def burn():
  account=request.args.get("account")
  rc=exec("burn one",account=account)
  return jsonify(rc)



if __name__ == '__main__':
  _port=int(sys.argv[1])

  CORS(app)

  if "debug" in sys.argv:
    app.run(debug=True,port=_port)
  else:
    if "ssl" in sys.argv:
      context = ssl.SSLContext(ssl.PROTOCOL_TLSv1_2)
      context.load_cert_chain("/certs/fullchain.pem", "/certs/privkey.pem")
      app = Flask(__name__, ssl_context=context)
      app.run(debug=False,port=_port)
    else:
      app.run(debug=False,port=_port)

  app.config.from_mapping({
    "DEBUG": True,          # some Flask specific configs
    "CACHE_TYPE": "SimpleCache",  # Flask-Caching related configs
    "CACHE_DEFAULT_TIMEOUT": 300
  })




