import base64

import requests.api

from settings import NFT_STORAGE_KEY


class NFTStorage:
  def __init__(self):
    pass


  def add(self,content,_type=None,filename=""):
    """
    voir https://nft.storage/api-docs/
    :param content:
    :param type:
    :return:
    """
    if type(content)==str:
      if _type is None:
        _type=content.split(";base64,")[0].split("data:")[1]
      data=base64.b64decode(content.split(";base64,")[1])
      service="upload"

    if type(content)==dict:
      data=content
      service="store"

    if type(content)==bytes:
      data=content
      service="upload"

    result=requests.api.post("https://api.nft.storage/"+service,data,headers={"Authorization":"Bearer "+NFT_STORAGE_KEY}).json()
    cid=result["value"]["cid"]
    url="https://"+cid+".ipfs.nftstorage.link"
    return {"cid":cid,"url":url+(("?"+filename) if len(filename)>0 else "")}
