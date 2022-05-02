import base64

import requests

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

    response = requests.post('https://ipfs.infura.io:5001/api/v0/add', files={"file":f.name},auth=(INFURA_PROJECT_ID, INFURA_PROJECT_SECRET))

    if removeFile:del f

    return response.json()["Hash"]
