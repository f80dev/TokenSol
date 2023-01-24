import base64
import hashlib
import json
from io import BytesIO
from os.path import exists
from urllib import parse

from PIL import Image

from flaskr.GitHubStorage import GithubStorage
from flaskr.dao import DAO

from flaskr.GoogleCloudStorageTools import GoogleCloudStorageTools
from flaskr.Tools import normalize, log, extract_from_dict, get_filename_from_content
from flaskr.infura import Infura
from flaskr.ipfs import IPFS
from flaskr.nftstorage import NFTStorage
from flaskr.secret import GITHUB_TOKEN
from flaskr.settings import IPFS_SERVER, TEMP_DIR


def upload_on_platform(data,platform="ipfs",id=None,options={},domain_appli="",domain_server="",github_token=GITHUB_TOKEN):
  """
  Charge une image sur une platforme
  :param data:
  :param platform:
  :param id:
  :param options:
  :param dao:
  :param domain_appli:
  :param domain_server:
  :param sticker:
  :return:

  A été pour l'instant supprimé
    if ext=="svg":
      sticker=Sticker(cid,text=str(b,"utf8"))
    else:
      sticker=Sticker(cid,data["content"],ext=ext)

  """
  rc=None

  b=None
  if type(data)==str:
    b=base64.b64decode(data.split("base64,")[1])
    data={"content":data,"type":"webp"}
  else:
    if "content" in data:
      if data["content"].startswith("data:"):
        b=base64.b64decode(data["content"].split("base64,")[1])
      else:
        b=bytes(data["content"],"utf8")


  if platform=="ipfs":
    ipfs=IPFS(IPFS_SERVER)
    cid=ipfs.add(data,removeFile=True)
    rc={"cid":cid["Hash"],"url":ipfs.get_link(cid["Hash"])+("?f="+parse.quote(cid["filename"]) if "filename" in cid else "")}


  if platform=="infura":
    infura=Infura()
    cid=infura.add(data)
    rc={"cid":cid["Hash"],"url":cid["url"]}
    if "filename" in cid: rc["filename"]=cid["filename"]


  if platform.startswith("db-"):
    cid=DAO(network=platform).add(data,domain_server=domain_server)
    rc={"cid":cid["Hash"],"url":cid["url"]}



  if platform=="server" or platform.startswith("nfluent"):
    if b:
      #Encodage du nom du fichier
      filename_encoded=str(base64.b64encode(bytes(data["filename"],"utf8")),"utf8") if "filename" in data and not "image" in data["type"] else ""
      filename=get_filename_from_content(data["content"],"store",data["type"])
      with open(TEMP_DIR+filename,"wb") as file: file.write(b)
      return {"cid":filename,"url":domain_server+"/api/images/"+filename+"?f="+filename_encoded}
      # else:
      #   img=Image.open(BytesIO(b))
      #   filename=extract_from_dict(data,"filename","")
      #   if filename is None or filename=="":filename=get_filename_from_content(b,"store",img.format.lower())
      #
      #   if not exists(TEMP_DIR+filename):
      #     img.save(TEMP_DIR+filename,save_all=True)

    else:

      if "_id" in data: del data["_id"]
      filename=get_filename_from_content(json.dumps(data),"store","json")
      if not exists(TEMP_DIR+filename):
        with open(TEMP_DIR+filename,"w") as file:
          json.dump(data,file)

    return {"cid":filename,"url":domain_server+"/api/images/"+filename}


  if platform=="nftstorage":
    if "content" in data:
      rc=NFTStorage().add(data["content"],data["type"])
    else:
      rc=NFTStorage().add(data)

  if platform=="googlecloud":
    rc=GoogleCloudStorageTools().add(data,id)

  if platform.startswith("github"):
    try:
      repo=extract_from_dict(options,"repository",platform.split("-")[2].strip())
      github_account=extract_from_dict(options,"account",platform.split("-")[1].strip())
      branch=extract_from_dict(options,"branch","main")
    except:
      log("La syntaxe doit être github-<account>-<repository>")
      return None

    try:
      github_storage=GithubStorage(repo,branch,github_account,github_token)
      rc=github_storage.add(data,id,overwrite=True)
    except:
      log("Impossible de pousser le contenu. Pour obtenir un token valide voir https://github.com/settings/tokens et accorder les propriétés admin:org et repo")

  return rc
