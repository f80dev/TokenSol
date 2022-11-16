import base64
from os.path import exists

import GitHubStorage
from GoogleCloudStorageTools import GoogleCloudStorageTools
from Tools import normalize, log
from infura import Infura
from ipfs import IPFS
from nftstorage import NFTStorage
from secret import GITHUB_TOKEN
from settings import IPFS_SERVER


def upload_on_platform(data,platform="ipfs",id=None,options={},dao=None,domain_appli="",domain_server="",sticker=None):
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

  if platform=="ipfs":
    ipfs=IPFS(IPFS_SERVER)
    cid=ipfs.add(data,removeFile=True)
    rc={"cid":cid["Hash"],"url":ipfs.get_link(cid["Hash"])+("?"+cid["Name"] if "Name" in cid else "")}

  if platform=="infura":
    infura=Infura()
    cid=infura.add(data)
    rc={"cid":cid["Hash"],"url":cid["url"]}

  if platform=="mongodb":
    cid=dao.add_dict(data)
    rc={"cid":cid,"url":domain_appli+"/api/json/"+cid}

  if platform.startswith("nfluent"):
    ext=data["type"].split("/")[1].split("+")[0]

    if "filename" in data and not data["filename"] is None and len(data["filename"])>0 and exists(data["filename"]):
      log("Le fichier est déjà présent sur le serveur")
      cid=data["filename"][data["filename"].rindex("/")+1:]
      return {"cid":cid,"url":domain_server+"/api/images/"+cid+"?"+ext}

    b=base64.b64decode(data["content"].split("base64,")[1])
    cid=hex(hash(data["content"]))+"."+ext
    filename=normalize(data["filename"].split(".")[0]+"_"+cid) if "filename" in data and not data["filename"] is None else cid


    sticker.save("./temp/"+filename)
    rc={"cid":cid,"url":domain_server+"/api/images/"+filename+"?"+ext}


  if platform=="nftstorage":
    if "content" in data:
      rc=NFTStorage().add(data["content"],data["type"])
    else:
      rc=NFTStorage().add(data)

  if platform=="googlecloud":
    rc=GoogleCloudStorageTools().add(data,id)

  if platform.startswith("github"):
    repo=options["repository"] if "repository" in options else platform.split("/")[1].strip()
    github_storage=GitHubStorage.GithubStorage(repo,"main","nfluentdev",GITHUB_TOKEN)
    rc= github_storage.add(data,id,overwrite=False)

  return rc
