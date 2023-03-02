from flaskr.Keys import Key
from flaskr.NFluentAccount import NfluentAccount
from flaskr.Tools import setParams, decrypt
from flaskr.ipfs import IPFS


class Network():
  network=""
  network_name=""
  network_type=""
  keys=[]

  def __init__(self,network:str):
    self.network=network
    self.network_name=network.split("-")[0]
    self.network_type=network.split("-")[1] if "-" in network else ""


  def add_keys(self,operation=None,user=None):
    if operation:
      for k in operation["keys"]:
        self.keys.append(decrypt(k))

    if user:
      self.keys=self.keys+user["keys"]


  def __str__(self):
    return self.network

  def reset(self,item:str="all"):
    raise NotImplementedError()

  def get_account(self,addr:str,solde:int=10) -> NfluentAccount:
    return NfluentAccount(address=addr,network=self.network,balance=100e18,nonce=0,unity="",explorer="")

  def can_mint(self,nft_to_mint,dest:str):
    return True

  def is_blockchain(self):
    return not self.network is None and not self.network.startswith("file-") and not self.network.startswith("db-")


  def mint(self, miner:Key, title,description, collection, properties: dict,ipfs:IPFS,files=[], quantity=1, royalties=0, visual="", tags="",price=0,symbol="NFluentToken"):
    raise NotImplementedError()


  def transfer(self,addr:str,miner:Key,owner:str):
    raise NotImplementedError("Fonction transfer")

  def create_account(self,email="",seed="",domain_appli="",
                 subject="Votre nouveau wallet est disponible",
                 mail_new_wallet="",mail_existing_wallet="",
                 send_qrcode_with_mail=True,
                 histo=None,send_real_email=True) -> Key:
    return email,"","",""


  def nfluent_wallet_url(self,address:str,domain_appli=""):
    if type(address)!=str: address=address.address.bech32()
    url=domain_appli+"/wallet/?" if "localhost" in domain_appli or "127.0.0.1" in domain_appli else "https://wallet.nfluent.io/?"
    return url+setParams({"toolbar":"false","network":self.network,"addr":address})


  def get_balance(self,address):
    raise NotImplementedError()

  def get_keys(self) -> [Key]:
    raise NotImplementedError()


  def burn(self,addr:str,miner:Key,n_token=1):
    return True



  def get_nfts(self,_user,limit=2000,with_attr=False,offset=0,with_collection=False):
    pass

  def get_collections(self,addr:str,detail=False,filter_type="NFT"):
    pass
