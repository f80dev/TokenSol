import hashlib
import json
import os
from os.path import exists

import yaml

from flaskr.Keys import Key
from flaskr.Network import Network
from flaskr.Storage import Storage

from flaskr.NFT import NFT
from flaskr.Tools import now, get_hash_from_content
from flaskr.secret import PASSWORD

FILE_PREFIX_ID="file_"

class StoreFile(Network,Storage):
  filename=""

  def __init__(self, network="file-mainnet",domain_server="",upload_dir=""):
    Network.__init__(self,network=network)
    Storage.__init__(self,domain_server=domain_server)
    self.filename=network.split("-")[1] if "-" in network else "storage"
    self.filename=(upload_dir+self.filename if not "/" in self.filename else self.filename)+".yaml"


  def __str__(self):
      return self.network

  def reset(self,item="all"):
    self.read()
    if item=="all":
      if exists(self.filename):
        os.remove(self.filename)
        return True
    else:
      if item in self.content:
        del self.content[item]
        self.write()
        return True

    return False


  def add(self,content,domain_server=None):
    self.read()

    content_for_key=json.dumps(content) if type(content)==dict else content
    key=FILE_PREFIX_ID+hashlib.sha256(bytes(content_for_key,encoding="utf8")).hexdigest()
    if not "storage" in self.content:self.content["storage"]={}
    self.content["storage"][key]=content

    self.write()

    rc={"cid":key}
    if self.domain_server:rc["url"]=self.domain_server+"/api/files/"+key
    return rc


  def get(self,key):
    self.read()
    if "storage" in self.content and key in self.content["storage"]:
      return self.content["storage"][key]
    return None


  def rem(self,key):
    self.read()
    if "storage" in self.content and key in self.content["storage"]:
      del self.content["storage"][key]
      self.write()
      return True
    return False


  def transfer(self,nft_addr:str,from_addr:str,to_addr:str):
    self.read()
    for pos in range(len(self.content["nfts"])):
      if self.content["nfts"][pos]["address"]==nft_addr:
        self.content["nfts"][pos]["owner"]=to_addr
        self.write()
        return True
    return False



  def get_nfts(self,owner="",limit=2000,with_attr=False,offset=0,with_collection=False):
    self.read()
    rc=list()
    for nft in self.content["nfts"]:
      _nft=NFT(object=nft)
      if _nft.owner==owner or len(owner)==0:
        rc.append(_nft)
    return rc

  def get_nft(self,addr,attr=True) -> NFT:
    """
    Retourne le détail d'un NFT
    :param addr:
    :param attr:
    :return:
    """
    self.read()
    for nft in self.content["nfts"]:
      if nft["address"]==addr:return NFT(object=nft)
    return None

  def write(self):
    with open(self.filename,"w",encoding="utf-8") as f:
      return yaml.dump(self.content,f)

  def read(self):
    if not exists(self.filename):
      self.content={"version":"1.0","nfts":[]}
    else:
      self.content=yaml.safe_load(open(self.filename,"r",encoding="utf8").read())

  def getExplorer(self,addr="",type="address") -> str:
    return ""

  def get_collections(self,addr:str,detail=False,filter_type="NFT"):
    self.read()
    rc=list()
    if "nfts" in self.content:
      for nft in self.content["nfts"]:
        if not nft["collection"]["id"] in rc:
          rc.append({"id":nft["collection"]["id"]})
    return rc


  def burn(self,nft_addr:str,miner:Key,n_burn=1):
    rc=False
    self.read()
    nft=self.get_nft(nft_addr)
    if nft.miner==miner.address:
      for pos in range(len(self.content["nfts"])-1):
        if self.content["nfts"][pos]["address"]==nft_addr:
          del self.content["nfts"][pos]
          rc=True

    self.write()
    return rc



  def get_keys(self) -> [Key]:
    self.read()
    if not "accounts" in self.content: return []
    return [Key(obj=x) for x in self.content["accounts"]]


  def create_account(self,email="",seed="",domain_appli="",
                     subject="Votre nouveau wallet est disponible",
                     mail_new_wallet="",mail_existing_wallet="",
                     send_qrcode_with_mail=True,
                     histo=None,send_real_email=True,solde=100) -> Key:
    self.read()

    addr=FILE_PREFIX_ID+get_hash_from_content(email)
    if not "accounts" in self.content:self.content["accounts"]=[]

    if addr not in [x["address"] for x in self.content["accounts"]]:
      obj={"address":addr,
           "amount":solde,
           "network":"file",
           "balance":solde*1e18,
           "unity":"DBC",              #DBCoin
           "secret_key":"myprivatekey_"+addr,
           "name":email.split("@")[0]}
      self.content["accounts"].append(obj)
      self.write()
    else:
      for x in self.content["accounts"]:
        if x["address"]==addr:
          obj=x

    return Key(obj["secret_key"],obj["name"],address=obj["address"],network="file")


  def mint(self, miner:Key, title, description, collection, properties: list,
           storage:str, files=[], quantity=1, royalties=0, visual="", tags="", creators=[],
           domain_server="",price=0,symbol="NFluentToken"):
    self.read()
    nft=NFT(title,miner.address,miner.address,"",collection,properties,description,tags,visual,creators,"",royalties,
            {"quantity":quantity,"price":0},files)

    if nft.address=="": nft.address=FILE_PREFIX_ID+now("hex")
    obj=nft.__dict__
    obj["collection"]={"id":obj["collection"]["id"]}
    obj["dtCreate"]=now()

    if not "nfts" in self.content:
      self.content["nfts"]=[obj]
    else:
      self.content["nfts"].append(obj)

    self.write()

    rc={
      "error":"",
      "tx":"",
      "result":{"transaction":"","mint":nft.address},
      "balance":0,
      "link_mint":"",
      "link_transaction":"",
      "out": yaml.dump(obj),
      "command":"insert"
    }
    return rc


