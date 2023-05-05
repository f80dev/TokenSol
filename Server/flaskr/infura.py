import base64
import io
import json
from io import BytesIO
from time import sleep

import requests

from flaskr.Storage import Storage
from flaskr.Tools import log
from flaskr.settings import INFURA_PROJECT_ID, INFURA_PROJECT_SECRET


class Infura(Storage):

  def __init__(self,upload_dir=""):
    Storage.__init__(self,"https://ipfs.io/ipfs/")
    self.upload_dir=upload_dir

  def add(self,body,removeFile=True,format="",overwrite=False):
    if type(body)!=dict: body={"value":body}

    f=BytesIO()
    if "filename" in body:
      log("On créé le fichier pour pouvoir l'envoyer sur ipfs via infura")

      filename=self.upload_dir+body["filename"]
      #f=open(filename,"wb")
      if not "content" in body and "file" in body: body["content"]=body["file"]
      f.write(base64.b64decode(body["content"].split(";base64,")[1]))
      #voir si nécessaire d'ajouter : headers={"Content-Type":"multipart/form-data"}
      #open(filename,"rb")
      #voir https://docs.infura.io/infura/networks/ipfs/http-api-methods/add
      response = requests.post('https://ipfs.infura.io:5001/api/v0/add',
                               files={"file":f},
                               auth=(INFURA_PROJECT_ID, INFURA_PROJECT_SECRET))
      rc=response.json()
      #voir https://docs.ipfs.tech/reference/http/gateway/
      rc["url"]="https://ipfs.io/ipfs/"+rc["Hash"]+"?filename="+body["filename"]  #on peut ajouter format et download comme parametre

    else: #https://www.w3schools.com/python/ref_requests_post.asp
      #headers={"Content-Type":"application/json"},
      f=io.StringIO()
      f.write(json.dumps(body))
      response = requests.post('https://ipfs.infura.io:5001/api/v0/add',
                               files={"file":f},
                               auth=(INFURA_PROJECT_ID, INFURA_PROJECT_SECRET))
      rc=response.json()
      rc["cid"]=rc["Hash"]
      rc["url"]="https://ipfs.io/ipfs/"+rc["cid"]

    if len(format)>0:rc["url"]=rc["url"]+"&format="+format
    return rc

  def get(self,key,format=""):
    """
    voir https://docs.ipfs.tech/reference/kubo/rpc/#api-v0-get
    :param key:
    :return:
    """
    for _try in range(20):
      #response = requests.get('https://ipfs.io/ipfs/'+key)
      url='https://ipfs.infura.io:5001/api/v0/get?arg='+key
      response = requests.post(url,
                              auth=(INFURA_PROJECT_ID, INFURA_PROJECT_SECRET))
      if response.status_code!=503:
        break
      else:
        sleep(3)

    if response.status_code==200:
      return response.json()
    else:
      return None


  def rem(self,key:str):
    """
    https://docs.ipfs.tech/reference/kubo/rpc/#api-v0-key-rm
    :param ley:
    :return:
    """
    return True
    #response = requests.post('https://ipfs.infura.io:5001/api/v0/key/rm?arg='+key,auth=(INFURA_PROJECT_ID, INFURA_PROJECT_SECRET))
    #return response.json()



  def get_link(self, cid):
    return "https://ipfs.io/ipfs/"+cid
