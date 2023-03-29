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
    if not "-" in network:network="elrond-"+network
    self.network_name=network.split("-")[0]
    self.network_type=network.split("-")[1]

  def get_accounts(self) -> [NfluentAccount]:
    rc=[]
    for k in self.get_keys():
      if not k.address is None and len(k.address)>0:
        rc.append(NfluentAccount(
          name=k.name,
          address=k.address,
          network=k.network,
          balance=self.get_balances(k.address),
          nonce=0,
          explorer=self.getExplorer(k.address,"address"),
          unity=self.get_unity()
        ))
    return rc

  def add_keys(self,operation=None,user=None):
    if operation:
      for k in operation["keys"]:
        self.keys.append(decrypt(k))

    if user:
      self.keys=self.keys+user["keys"]


  def __str__(self):
    return self.network

  def reset(self,item:str="all"):
    return True

  def get_account(self,addr:str,solde:int=10) -> NfluentAccount:
    return NfluentAccount(address=addr,network=self.network,balance=100e18,nonce=0,unity="",explorer="")

  def can_mint(self,nft_to_mint,dest:str):
    return True

  def is_blockchain(self):
    return not self.network is None and not self.network.startswith("file-") and not self.network.startswith("db-")


  def mint(self, miner:Key, title,description, collection:dict, properties: dict,ipfs:IPFS,files=[], quantity=1, royalties=0, visual="", tags="",price=0,symbol="NFluentToken"):
    raise NotImplementedError()


  def canMintOnCollection(self,miner_addr:str,collection:dict,quantity=1):  #Pour l'ensemble des réseaux excepté Elrond c'est toujours vrai
    return True

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


  def get_balances(self, address):
    raise NotImplementedError()

  def get_keys(self) -> [Key]:
    raise NotImplementedError()


  def add_collection(self, owner:Key, collection_name:str,options:list=[],type_collection="SemiFungible") -> (dict):
    return {"id":collection_name,"name":collection_name}

  def burn(self,addr:str,miner:Key,n_token=1):
    return True


  def has_nft(self,owner:str,nft_addr:str):
    nft=self.get_nft(nft_addr)
    return nft.owner==owner

  def find_key(self,addr) -> Key:
    for k in self.get_keys():
      if k.address==addr or k.name==addr: return k
    return None

  def get_nfts(self,_user,limit=2000,with_attr=False,offset=0,with_collection=False):
    pass

  def get_collections(self,addr:str,detail=False,type_collection="NFT",special_role=""):
    return [
         {"id":self.network_name+"Collection","name":self.network_name+"colname","owner":self.network_name}
       ]


  def create_transaction(self,error="",hash="",nft_addr=""):
    rc={
      "id":hash,
      "tx":hash,
      "error":error,
      "hash":hash,
      "explorer":self.getExplorer(hash,"explorer") if len(hash)>0 else ""
    }
    if len(nft_addr)>0:rc["nft"]=nft_addr
    return rc