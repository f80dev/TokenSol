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


def upload_on_platform(data,platform="ipfs",id=None,upload_dir="",domain_server="",api_key="") -> dict:
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

  if type(data)==dict and "file" in data and "filename" in data: data["content"]=data["file"]

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


  if platform.startswith("db-") or platform.startswith("dao-"):
    cid=DAO(network=platform,domain_server=domain_server).add(data)
    url=cid["url"]
    if "filename" in data:url=url+"?f="+str(base64.b64encode(bytes(data["filename"],"utf8")),"utf8") if "url" in cid else ""
    rc={
      "cid":cid["cid"],
      "url":url
      }


  if platform.startswith("server") or platform.startswith("nfluent") or platform=="file":
    if b and type(data)==dict and "filename" in data:
      #Encodage du nom du fichier
      filename_encoded=str(base64.b64encode(bytes(data["filename"],"utf8")),"utf8") if "filename" in data and not "image" in data["type"] else ""
      if "file" in data: data["content"]=data["file"]
      filename=get_filename_from_content(data["content"],"store",data["type"])
      with open(upload_dir+filename,"wb") as file: file.write(b)
      return {"cid":filename,"url":domain_server+"/api/files/"+filename+("?f="+filename_encoded if len(filename_encoded)>0 else "")}

      # else:
      #   img=Image.open(BytesIO(b))
      #   filename=extract_from_dict(data,"filename","")
      #   if filename is None or filename=="":filename=get_filename_from_content(b,"store",img.format.lower())
      #
      #   if not exists(TEMP_DIR+filename):
      #     img.save(TEMP_DIR+filename,save_all=True)

    if type(data)!=dict: data=data.__dict__
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
      github_storage=GithubStorage(platform=platform,token=api_key)
    except:
      log("La syntaxe doit être github-<account>-<repository>")
      return None
    try:
      rc=github_storage.add(data,id,overwrite=True)
    except Exception as inst:
      log("Impossible de pousser le contenu. Pour obtenir un token valide voir https://github.com/settings/tokens et accorder les propriétés admin:org et repo")
      rc={"error":str(inst.args)}

  return rc
