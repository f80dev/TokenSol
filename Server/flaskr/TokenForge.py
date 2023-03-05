import base64
import json
from os.path import exists
from urllib import parse
import PIL.Image
from flaskr.GitHubStorage import GithubStorage
from flaskr.StoreFile import StoreFile
from flaskr.dao import DAO

from flaskr.GoogleCloudStorageTools import GoogleCloudStorageTools
from flaskr.Tools import log, extract_from_dict, get_filename_from_content
from flaskr.infura import Infura
from flaskr.ipfs import IPFS
from flaskr.nftstorage import NFTStorage
from flaskr.secret import GITHUB_TOKEN
from flaskr.settings import IPFS_SERVER


def upload_on_platform(data,platform="ipfs",id=None,options={},upload_dir="",domain_server="",github_token=GITHUB_TOKEN) -> dict:
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
    if "base64" in data:
      b=base64.b64decode(data.split("base64,")[1])
      data={"content":data,"type":"webp"}
    else:
      b=bytes(data,"utf8")

  if type(data)==dict and "content" in data:
    if data["content"].startswith("data:"):
      b=base64.b64decode(data["content"].split("base64,")[1])
    else:
      b=bytes(data["content"],"utf8")


  if platform=="ipfs":
    ipfs=IPFS(IPFS_SERVER)
    cid=ipfs.add(data,removeFile=True)
    rc={"cid":cid["Hash"],"url":ipfs.get_link(cid["Hash"])+("?f="+parse.quote(cid["filename"]) if "filename" in cid else "")}


  if platform=="infura":
    infura=Infura(upload_dir=upload_dir)
    cid=infura.add(data)
    rc={"cid":cid["Hash"],"url":cid["url"]}
    if "filename" in cid: rc["filename"]=cid["filename"]


  if platform.startswith("db-"):
    cid=DAO(network=platform,domain_server=domain_server).add(data)
    rc={
      "cid":cid["cid"],
      "url":cid["url"]+"?f="+str(base64.b64encode(bytes(data["filename"],"utf8")),"utf8") if "url" in cid else ""
      }


  if platform=="server" or platform.startswith("nfluent") or platform=="file":
    if b and type(data)==dict and "content" in data:
      #Encodage du nom du fichier
      filename_encoded=str(base64.b64encode(bytes(data["filename"],"utf8")),"utf8") if "filename" in data and not "image" in data["type"] else ""
      filename=get_filename_from_content(data["content"],"store",data["type"])
      with open(upload_dir+filename,"wb") as file: file.write(b)
      return {"cid":filename,"url":domain_server+"/api/images/"+filename+("?f="+filename_encoded if len(filename_encoded)>0 else "")}

      # else:
      #   img=Image.open(BytesIO(b))
      #   filename=extract_from_dict(data,"filename","")
      #   if filename is None or filename=="":filename=get_filename_from_content(b,"store",img.format.lower())
      #
      #   if not exists(TEMP_DIR+filename):
      #     img.save(TEMP_DIR+filename,save_all=True)

    else:
      return StoreFile(domain_server=domain_server).add(data)


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
