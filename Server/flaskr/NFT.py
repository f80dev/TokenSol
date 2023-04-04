import base64
import json
import yaml
from PIL import Image

from flaskr.Tools import extract_from_dict, decrypt


class NFT:
  collection:dict
  attributes:list
  name:str
  symbol=""
  dtCreate:int=0
  description:str=""
  tags:str
  visual:str=""
  creators:list
  address:str=None
  miner:str=""
  royalties:int
  owner:str=""
  marketplace:dict={}
  network="elrond-devnet"
  files:list
  other:dict={}
  balances:dict={}

  def __init__(self,
               name: str="",
               miner:str="",
               owner:str="",
               symbol: str="",
               collection: dict={},
               attributes: list=list(),
               description: str="",
               tags:str="",
               visual: str="",
               creators: list=list(),
               address: str="",
               royalties: int=0,
               price=0,
               supply=1,
               files:list=[],
               dtCreate:int=0,
               object=None) -> object:

    if not object is None:
      if "encrypt" in object:
        object=yaml.load(decrypt(object["encrypt"]),yaml.FullLoader)

      name=extract_from_dict(object,["name","title"],"NFT")
      dtCreate=object["dtCreate"] if "dtCreate" in object else 0
      symbol=extract_from_dict(object,["symbol","identifier"],"")
      description=extract_from_dict(object,"description","")
      visual=extract_from_dict(object,"visual,image,storage,url","")

      miner=extract_from_dict(object,["miner","creator"],"")

      if "properties" in object and "creators" in object["properties"]:object["creators"]=object["properties"]["creators"]
      creators=extract_from_dict(object,"creators",[])

      files=extract_from_dict(object,["files","uris"],[])
      attributes=object["attributes"] if "attributes" in object else []

      if "collection" in object:
        if type(object["collection"])==str:
          collection={"id":object["collection"]}
        else:
          collection=object["collection"]
      else:
          collection={}

      if not "owner" in collection:collection["owner"]=miner

      supply=int(extract_from_dict(object,["supply"],1))
      price=extract_from_dict(object,"price")

      royalties=extract_from_dict(object,["seller_fee_basis_points","royalties"],0)
      address=extract_from_dict(object,["address","id","identifier"],"")

      owner=object["owner"] if "owner" in object else ""
      self.other=object["other"] if "other" in object else {}
      self.tags=object["tags"] if "tags" in object else ""

    self.name=name
    self.description=description
    self.collection=collection
    self.balances={owner:1}
    if type(attributes)==str:attributes={"value":attributes}
    if type(attributes)==dict: attributes=[attributes]

    self.attributes=attributes
    self.supply=supply
    self.price=price
    self.miner=miner
    self.owner=owner
    self.symbol=symbol
    self.visual=visual
    self.creators=creators
    self.address=address
    self.tags=tags
    self.royalties=royalties

    try:
      self.files=[str(base64.b64decode(f),"utf8") for f in files]
    except:
      self.files=files

    self.dtCreate=dtCreate
    if self.visual is None or len(self.visual)==0: self.visual="https://hackernoon.imgix.net/images/0*kVvpU6Y4SzamDGVF.gif"




  def __str__(self):
    rc=self.address if not self.address is None else "NoAddresse"
    if self.symbol: rc=rc+" ("+self.symbol+")"
    return rc

  def toJson(self):
    return json.dumps(self, default=lambda o: o.__dict__,sort_keys=True, indent=4)

  def get_price(self):
    return self.marketplace["price"] if "price" in self.marketplace else 0

  def get_quantity(self):
    return self.marketplace["quantity"] if "quantity" in self.marketplace else 0

  def add_attribute(self,key:str,value:str):
    self.attributes.append({"trait_type":key,"value":value})

  def is_minted(self):
    return len(self.address)>0 and not self.address.startswith("db_")

  def toYAML(self):
    _d=self.__dict__
    return yaml.safe_dump(_d)



