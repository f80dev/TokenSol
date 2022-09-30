import json

from fontTools.ttLib import TTFont
from reportlab.pdfbase import pdfmetrics

from Tools import get_fonts


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
  other:dict={}

  def __init__(self, name: str="",
               symbol: str="",
               collection: dict={},
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
      self.visual=object["visual"] if "visual" in object else object["image"]
      if self.visual=="": self.visual=object["visual"] if "visual" in object else ""

      self.creators=object["creators"]
      self.files=object["files"] if "files" in object else []
      self.attributes=object["attributes"]
      self.collection=object["collection"] if "collection" in object else ""
      self.marketplace=object["marketplace"] if "marketplace" in object else {"price":0,"quantity":1,"max_mint":1}
      self.royalties=int(object["seller_fee_basis_points"]) if "seller_fee_basis_points" in object else (object["royalties"] if "royalties" in object else 0)
      self.address=object["address"] if "address" in object else ""      #Données obligatoire
      self.network=object["network"]
      self.owner=object["owner"] if "owner" in object else ""
      self.other=object["other"] if "other" in object else {}



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

  def is_minted(self):
	  return len(self.address)>0 and not self.address.startswith("db_")


