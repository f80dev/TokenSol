import base64
import json

import requests
from ipfshttpclient import multipart

from settings import INFURA_PROJECT_ID, INFURA_PROJECT_SECRET


class Infura:
  def __init__(self):
    pass

  def add(self,body,removeFile=True):
    if type(body)==dict:
      if "filename" in body:
        f=open("./Temp/"+body["filename"],"wb")
        f.write(base64.b64decode(body["content"].split(";base64,")[1]))
        f.close()
      else:
        f=open("./temp/temp.json","w")
        json.dump(body,f)
        f.close()


    data=json.dumps(body).encode("utf-8")
    response = requests.post('https://ipfs.infura.io:5001/api/v0/add',files={"file":data},auth=(INFURA_PROJECT_ID, INFURA_PROJECT_SECRET))
    #response = requests.post('https://ipfs.infura.io:5001/api/v0/put',body,auth=(INFURA_PROJECT_ID, INFURA_PROJECT_SECRET))

    rc=response.json()
    rc["url"]="https://ipfs.io/ipfs/"+rc["Hash"]
    return rc



  def get_link(self, cid):
    return "https://ipfs.io/ipfs/"+cid
