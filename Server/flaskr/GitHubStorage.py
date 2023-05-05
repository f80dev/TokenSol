import base64
import hashlib
import json
from json import dumps
from urllib import request

import requests
from github import Github

from flaskr.Storage import Storage
from flaskr.Tools import log, get_filename_from_content, now, get_hash
from flaskr.secret import GITHUB_TOKEN


class GithubStorage(Storage):
  """
  Stockage sur Github
  https://pygithub.readthedocs.io/en/latest/examples/Repository.html#create-a-new-file-in-the-repository
  """
  api: Github=None
  def __init__(self,repo="storage", branch="main", login="nfluentdev",token="",platform=""):
    self.token=token if len(token)>0 else GITHUB_TOKEN
    if len(platform)>0:
      login=platform.split("-")[1]
      repo=platform.split("-")[2]
      branch=platform.split("-")[3] if len(platform.split("-"))>3 else "main"

    self.repo=repo
    self.branch=branch if branch else "main"
    self.login=login

    try:
      self.api = Github(self.token).get_user(self.login).get_repo(self.repo)
      log("Stockage github activé avec le token "+self.token+" : voir le dépôt https://github.com/"+self.login+"/"+self.repo)
    except Exception as inst:
      log("Probleme de connexion avec "+self.token+" pour "+self.login + "/"+ self.repo+" : "+str(inst))


  def __del__(self):
    self.api=None


  def get(self,cid:str):
    #voir https://pygithub.readthedocs.io/en/latest/github_objects/Repository.html?highlight=get_contents#github.Repository.Repository.get_contents
    #url="https://raw.githubusercontent.com/"+self.login+"/"+self.repo+"/"+self.branch+"/"+cid
    bytes=self.api.get_contents(cid,ref=self.branch).decoded_content
    if cid.endswith("json"): return json.loads(str(bytes,"utf8"))
    return bytes


  def get_sha(self,cid):
    rc=self.api.get_contents(cid,ref=self.branch)
    return rc.sha

  def rem(self,cid:str):
    sha=self.get_sha(cid)
    rc=self.api.delete_file(path=cid,message="Demande de suppression",branch=self.branch,sha=sha)
    return rc


  def add(self,data:dict,id=None,overwrite=False):
    ext=""

    if type(data)==bytes:
      content=data
      ext=""

    if type(data)==dict:
      if "filename" in data and "file" in data: data["content"]=data["file"]
      if "content" in data and "filename" in data:
        id=now("random")[5:8]+"_"+data["filename"]
        ext=data["filename"][data["filename"].rindex(".")+1:]
        data=data["content"]
      else:
        ext="json"
        content=dumps(data)

    if type(data)==str:
      if data.startswith("http"):
        req=requests.get(data)
        file_type=req.headers["Content-Type"]
        ext=file_type.split("image/")[1]
        content=req.content
      else:
        content=base64.b64decode(data.split("base64,")[1])
        if data.startswith("data:image") and len(ext)==0:
          ext=data.split("image/")[1].split(";")[0]

    if id is None or len(id)==0:id=get_filename_from_content(content,ext=ext)
    if "/" in id:id=id[id.rindex("/")+1:]

    url="https://raw.githubusercontent.com/"+self.login+"/"+self.repo+"/"+self.branch+"/"+id
    log("Ecriture de "+url)

    try:
      if overwrite:
        ct = self.api.get_contents(id,ref=self.branch)
        result=self.api.update_file(ct.path,"maj",content,ct.sha,self.branch)
      else:
        contents = self.api.get_contents(id,ref=self.branch)
    except Exception as inst:
      rc=self.api.create_file(id,"create",content,branch=self.branch)

    return {"cid":id,"url":url,"hash":get_hash(content)}



