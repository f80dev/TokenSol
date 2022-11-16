from Tools import setParams
from ipfs import IPFS


class Network():
  network=""

  def __init__(self,network:str):
    self.network=network

  def mint(self, miner, title,description, collection, properties: dict,ipfs:IPFS,files=[], quantity=1, royalties=0, visual="", tags=""):
    pass


  def nfluent_wallet_url(self,address:str,domain_appli=""):
    url=domain_appli+"/wallet/?" if "localhost" in domain_appli or "127.0.0.1" in domain_appli else "https://wallet.nfluent.io/?"
    return url+setParams({"toolbar":"false","network":self.network,"addr":address})


  def get_keys(self,qrcode_scale=0,with_balance=False):
    pass

  def get_nfts(self,_user,limit=2000,with_attr=False,offset=0,with_collection=False):
    pass
