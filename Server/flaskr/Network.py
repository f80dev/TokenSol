from flaskr.Tools import setParams
from flaskr.ipfs import IPFS


class Network():
  network=""

  def __init__(self,network:str):
    self.network=network


  def mint(self, miner, title,description, collection, properties: dict,ipfs:IPFS,files=[], quantity=1, royalties=0, visual="", tags=""):
    raise NotImplementedError()


  def nfluent_wallet_url(self,address:str,domain_appli=""):
    if type(address)!=str: address=address.address.bech32()
    url=domain_appli+"/wallet/?" if "localhost" in domain_appli or "127.0.0.1" in domain_appli else "https://wallet.nfluent.io/?"
    return url+setParams({"toolbar":"false","network":self.network,"addr":address})

  def getExplorer(self,addr="",type="address") -> str:
    raise NotImplementedError()

  def get_balance(self,address):
    raise NotImplementedError()

  def get_keys(self,qrcode_scale=0,with_balance=False):
    raise NotImplementedError()

  def get_nfts(self,_user,limit=2000,with_attr=False,offset=0,with_collection=False):
    raise NotImplementedError()

  def get_collections(self,addr:str,detail=False,filter_type="NFT"):
    raise NotImplementedError()
