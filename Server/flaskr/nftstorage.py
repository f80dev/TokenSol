import base64
from json import dumps

import requests.api

from flaskr.Keys import Key
from flaskr.settings import NFT_STORAGE_KEY


class NFTStorage:
  def __init__(self):
    pass

  def get(self,cid:str):
    url="https://<cid>.ipfs.nftstorage.link/".replace("<cid>",cid)
    result=requests.api.get(url)
    if result.status_code==200:
      return result.json()
    else:
      return None

  def rem(self,cid):
    """
    voir https://nft.storage/api-docs/
    :param cid:
    :return:
    """
    return True


  def add(self,content,_type=None,filename=""):
    """
    voir https://nft.storage/api-docs/
    :param content:
    :param type:
    :return:
    """
    content_type="image/webp"
    if type(content)==str:
      if "<svg" in content: content_type="image/svg"
      if _type is None:
        if "data:" in content:
          _type=content.split(";base64,")[0].split("data:")[1]
        else:
          _type="plain/text"

      if "base64," in content:
        content=base64.b64decode(content.split(";base64,")[1])
      else:
        if not "<svg" in content:
          content={"value":content}
        else:
          data=content

      service="upload"

    if type(content)==dict:
      data=dumps(content)
      content_type="application/octet-stream"
      service="upload"

    if type(content)==bytes:
      data=content
      service="upload"

    result=requests.api.post("https://api.nft.storage/"+service,data,
                             headers={
                               "Authorization":"Bearer "+NFT_STORAGE_KEY,
                               "Content-Type": content_type
                             }).json()
    cid=result["value"]["cid"]
    url="https://"+cid+".ipfs.nftstorage.link"
    return {"cid":cid,"url":url+(("?"+filename) if len(filename)>0 else "")}
