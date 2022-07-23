import json


class NFT:
  collection:dict
  attributes:list
  name:str
  description:str
  visual:str
  creators:list
  address:str
  royalties:int
  owner:str=""
  amount:int=1
  marketplace:dict={}
  network="elrond-devnet"
  files:list

  def __init__(self, name: str="",
               symbol: str="",
               collection: dict=dict(),
               attributes: list=list(),
               description: str="",
               visual: str="",
               creators: list=list(),
               address: str="",
               royalties: int=0,
               marketplace:dict={},
               object=None) -> object:
    if object is None:
      self.name=name
      self.description=description
      self.collection=collection
      self.attributes=attributes
      self.symbol=symbol
      self.visual=visual
      self.creators=creators
      self.address=address
      self.royalties=royalties
      self.marketplace=marketplace
    else:
      self.name=object["name"]
      self.symbol=object["symbol"]
      self.description=object["description"]
      self.visual=object["image"]
      self.attributes=object["attributes"]
      self.collection=object["collection"]
      self.marketplace=object["marketplace"]

  def toJson(self):
    return json.dumps(self, default=lambda o: o.__dict__,sort_keys=True, indent=4)

  def toString(self):
    return self.name+" "+self.symbol

  def get_price(self):
    return self.marketplace["price"] if "price" in self.marketplace else 0

  def get_quantity(self):
    return self.marketplace["quantity"] if "quantity" in self.marketplace else 0

  def add_attribute(self,key:str,value:str):
    self.attributes.append({"trait_type":key,"value":value})


