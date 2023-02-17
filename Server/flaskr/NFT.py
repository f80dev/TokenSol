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
  amount:int=1
  marketplace:dict={}
  network="elrond-devnet"
  files:list
  other:dict={}

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
               marketplace:dict={"quantity":1,"price":0},
               files:list=[],
               dtCreate:int=0,
               object=None,
               image=None) -> object:

    if not object is None:
      if "encrypt" in object:
        object=yaml.load(decrypt(object["encrypt"]),yaml.FullLoader)

      self.name=extract_from_dict(object,["name","title"],"NFT")
      self.dtCreate=object["dtCreate"] if "dtCreate" in object else 0
      self.symbol=extract_from_dict(object,"symbol","")
      self.description=extract_from_dict(object,"description","")
      self.visual=extract_from_dict(object,"visual,image,storage","")
      self.miner=extract_from_dict(object,"miner","")

      if "properties" in object and "creators" in object["properties"]:object["creators"]=object["properties"]["creators"]
      self.creators=extract_from_dict(object,"creators",[])

      self.files=extract_from_dict(object,"files",[])
      self.attributes=object["attributes"] if "attributes" in object else ""
      self.collection=object["collection"] if "collection" in object else ""
      self.marketplace=object["marketplace"] if "marketplace" in object else {"price":0,"quantity":1,"max_mint":1}
      self.royalties=int(object["seller_fee_basis_points"]) if "seller_fee_basis_points" in object else (object["royalties"] if "royalties" in object else 0)
      self.address=object["address"] if "address" in object else ("db_"+str(object["_id"]) if "_id" in object else "")     #Données obligatoire
      self.network=object["network"] if "network" in object else ""
      self.owner=object["owner"] if "owner" in object else ""
      self.other=object["other"] if "other" in object else {}
      self.tags=object["tags"] if "tags" in object else ""
    else:
      self.name=name
      self.description=description
      self.collection=collection
      if type(attributes)==str:attributes={"value":attributes}
      if type(attributes)==dict: attributes=[attributes]
      self.attributes=attributes
      self.miner=miner
      self.owner=owner
      self.symbol=symbol
      self.visual=visual
      self.creators=creators
      self.address=address
      self.tags=tags
      self.royalties=royalties
      self.marketplace=marketplace
      try:
        self.files=[str(base64.b64decode(uri),"utf8") for uri in files]
      except:
        self.files=files
      self.dtCreate=dtCreate

      if image:
        img=Image.open(image)



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



