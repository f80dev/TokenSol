import base64
import json

import requests

from flaskr.Storage import Storage
from flaskr.Tools import log
from flaskr.settings import INFURA_PROJECT_ID, INFURA_PROJECT_SECRET, TEMP_DIR


class Infura(Storage):
  def __init__(self):
    pass

  def add(self,body,removeFile=True):
    if type(body)==dict:
      if "filename" in body:
        log("On créé le fichier pour pouvoir l'envoyer sur ipfs via infura")
        f=open(TEMP_DIR+body["filename"],"wb")
        f.write(base64.b64decode(body["content"].split(";base64,")[1]))
        f.close()

      else:
        f=open(TEMP_DIR+"temp.json","w")
        json.dump(body,f)
        f.close()

    data=json.dumps(body).encode("utf-8")
    response = requests.post('https://ipfs.infura.io:5001/api/v0/add',files={"file":data},auth=(INFURA_PROJECT_ID, INFURA_PROJECT_SECRET))
    #response = requests.post('https://ipfs.infura.io:5001/api/v0/put',body,auth=(INFURA_PROJECT_ID, INFURA_PROJECT_SECRET))

    rc=response.json()
    rc["url"]="https://ipfs.io/ipfs/"+rc["Hash"]+("?"+body["type"] if "type" in body else "")
    if "filename" in body: rc["filename"]=body["filename"]
    return rc



  def get_link(self, cid):
    return "https://ipfs.io/ipfs/"+cid
