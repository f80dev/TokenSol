from os import listdir

import requests
from eth_account import Account
from solcx import compile_source, install_solc
from web3.contract import Contract
from web3.middleware import geth_poa_middleware

from NFT import NFT
from Network import Network

from Tools import log, get_qrcode, send_mail, open_html_file, get_access_code_from_email
from dao import DAO
from ipfs import IPFS
from web3 import Web3, HTTPProvider

from secret import POLYGON_SCAN_API_KEY

POLYGON_KEY_DIR="./Polygon/Keys/"
install_solc(version='latest')


class Polygon (Network):

  abi=None
  metadata_cache={}

  def __init__(self,network="polygon-devnet"):
    super().__init__(network)
    rpc="https://rpc-mumbai.maticvigil.com" if "devnet" in network else "https://polygon-rpc.com"
    self.w3=Web3(HTTPProvider(rpc))
    self.w3.middleware_onion.inject(geth_poa_middleware, layer=0)
    if not self.w3.isConnected():
      log("Connexion impossible a "+rpc)


  def send_transaction(self,method,account) -> str:
    _account=self.toAccount(account)
    gas_needed=method.estimate_gas({"from":_account.address})
    transac=method.build_transaction({"from":_account.address,"gas":gas_needed,"nonce":self.w3.eth.getTransactionCount(_account.address)})
    sign_transac=self.w3.eth.account.sign_transaction(transac,private_key=_account.privateKey)
    tx_hash =self.w3.eth.sendRawTransaction(sign_transac.rawTransaction)
    self.w3.eth.waitForTransactionReceipt(tx_hash)
    log("Execution de la transaction : "+self.getExplorer(tx_hash.hex(),"tx"))

    return tx_hash.hex()


  def init_contract_interface(self):
    src=open("./Polygon/Master/contracts/NFTCollection.sol","r").read()
    libs=["@openzeppelin=./Polygon/Master/node_modules/@openzeppelin"]
    contract_id, contract_interface = compile_source(src,output_values=["abi","bin"],import_remappings=libs).popitem()
    return contract_interface


  def deploy_contract(self,miner,contract_interface,name,symbol,uri) -> Contract :
    abi=contract_interface['abi']
    bytecode=contract_interface['bin']
    _miner=self.toAccount(miner)
    constructor_contract=self.w3.eth.contract(abi=abi,bytecode=bytecode).constructor(uri,name,symbol)
    _tx=self.send_transaction(constructor_contract,miner)

    addr=self.w3.eth.get_transaction_receipt(_tx)['contractAddress']
    _contract=self.w3.eth.contract(address=addr,abi=abi)
    log("contract sur "+self.getExplorer(addr)+" deployé avec les fonctions "+str(_contract.functions.__dict__.keys()))

    log("Analyse du contrat : "+self.getExplorer(addr,"token"))

    return _contract


  def polygon_scan(self,address,action="txlist",module="account"):
    url="https://api-testnet.polygonscan.com/api?module="+module+"&action="+action+"&address="+address+"&startblock=0&endblock=99999999&page=1&offset=0&sort=asc&apikey="+POLYGON_SCAN_API_KEY
    if "mainnet" in self.network:url=url.replace("-testnet","")
    result=requests.get(url)

    rc=[]
    if result.status_code==200:
      for t in result.json()["result"]:
        t["explorer"]=self.getExplorer(t["hash"],"tx")
        rc.append(t)
    return rc


  def get_transactions(self,address,history_size=100,offset=0,type_address="account"):
    """
    test:
    voir https://api.polygonscan.com/api?module=tokennfttx&action=txlist&address=0xb91dd8225Db88dE4E3CD7B7eC538677A2c1Be8Cb&startblock=0&endblock=99999999&page=1&offset=10&sort=asc&apikey=YourApiKeyToken
    voir la documentation sur https://docs.polygonscan.com/api-endpoints/accounts
    :param address:
    :param history_size:
    :param offset:
    :return:
    """

    return self.polygon_scan(address,"txlist")


  def get_metadata(self,uri):
    if uri is None:return None

    if not uri in self.metadata_cache:
      metadata=requests.get(uri,timeout=60000)
      if metadata.status_code==200:
        self.metadata_cache[uri]=metadata.json()
      else:
        return None

    return self.metadata_cache[uri]


  def get_nft(self,addr):
    contract_addr=addr.split("-")[0]
    log("Récupération du contract "+self.getExplorer(contract_addr))

    nonce=addr.split("-")[1]

    if not self.abi: self.abi=self.init_contract_interface()["abi"]

    _contract=self.w3.eth.contract(address=self.w3.toChecksumAddress(contract_addr),abi=self.abi)

    metadata=self.get_metadata(_contract.functions.baseTokenURI().call())
    if not metadata is None:
      _nft=NFT(name=metadata["name"],
               description=metadata["description"],
               visual=metadata["image"],
               attributes=metadata["attributes"],
               address=addr,
               creators=metadata["creators"] if "creators" in metadata else [],
               marketplace=metadata["marketplace"] if "marketplace" in metadata else {"price":0,"quantity":1},
               royalties=100
               )
      return _nft
    else:
      return None


  def get_nfts(self,_user,limit=2000,with_attr=False,offset=0,with_collection=False):
    rc=[]
    _user=self.toAccount(_user)
    if _user:
      nfts=self.polygon_scan(_user.address,"tokennfttx")
      for t in nfts[offset:limit]:
        _nft=self.get_nft(t["contractAddress"]+"-"+t['tokenID'])
        _nft.symbol=t["tokenSymbol"]
        _nft.owner=t["to"]

        rc.append(_nft)

    return rc



  def compile(self,miner:str,title,symbol,uri) -> Contract:
    """
    deploiement voir https://docs.moonbeam.network/builders/build/eth-api/libraries/web3py/
    :param miner:
    :param title:
    :param symbol:
    :param uri:
    :return:
    """
    contract_interface = self.init_contract_interface()
    self.abi=contract_interface["abi"]
    contract = self.deploy_contract(miner,contract_interface,title,symbol,uri)
    return contract



  def opensea_metadata(self,title,description,visual,properties,animation_url="",collection="",price=0,quantity=1,creators=[],tags=""):
    """
    voir https://docs.opensea.io/docs/metadata-standards
    :return:
    """

    attributes=[]
    if type(properties)==dict:
      for k in properties.keys():
        attributes.append({"trait_types":k,"value":properties[k]})
    else:
      attributes=properties

    rc={
      "description":description,
      "animation_url":animation_url,
      "external_url": "",
      "image": visual,
      "name": title,
      "tags":tags,
      "attributes": attributes,
      "collection":{"name":collection},
      "marketplace":{"price":price,"quantity":quantity},
      "creators":creators
    }
    #Collection et marketplace ne font pas partie de la norme proposé par solana
    return rc


  def mint(self, miner, title,description, collection, properties: dict,ipfs:IPFS,files=[], quantity=1, royalties=0, visual="", tags="",creators=[]):
    #properties["tag"]=tags
    #properties["royalties"]=royalties
    cid=ipfs.add(self.opensea_metadata(title,description,visual,properties,collection=collection,creators=creators,tags=tags))
    contract=self.compile(miner,title,"symbol",cid["url"])
    rc=self.send_transaction(contract.functions.mintNFTs(quantity),miner)
    return rc



  def balance(self,account):
    return self.w3.eth.get_balance(account)/1e18


  def getExplorer(self,address:str,type_param="address"):
    return "https://"+("mumbai." if "devnet" in self.network else "")+"polygonscan.com/"+type_param+"/"+address


  def getNFTExplorer(self,address:str,type_param="assets"):
    return "https://"+\
           ("testnets." if "devnet" in self.network else "")+\
           ".opensea.io/"+ type_param + "/" + \
           ("mumbai" if "devnet" in self.network else "")+ \
           "/"+address


  def create_account(self,email="",seed="",domain_appli="",
                         subject="Votre compte Polygon est disponible",histo:DAO=None,
                          mail_content="mail_new_account",mail_existing_account="mail_existing_account"):
    """
    :param fund:
    :param name:
    :param seed_phrase:
    :return: Account, PEM,words,qrcode
    """
    log("Création d'un nouveau compte sur "+self.network)

    if histo:
      pubkey=histo.get_address(email,self.network)
      if pubkey:
        _u:Account=self.w3.eth.account.create()
        send_mail(open_html_file(mail_existing_account,{
          "wallet_address":pubkey,
          "mini_wallet":self.nfluent_wallet_url(pubkey,domain_appli),
          "url_explorer":self.getExplorer(pubkey)
        },domain_appli=domain_appli),email,subject=subject)
        _u.address=pubkey
        return _u,None,None,None

    if len(seed) == 0:
      _u:Account=self.w3.eth.account.create()
      address = _u.address
    else:
      _u=self.w3.eth.account.create_with_mnemonic(passphrase=seed)
      secret_key=_u.key
      pubkey = _u.address
      words=seed
      _u.secret_key=secret_key.hex()

    log("Création du compte "+self.getExplorer(pubkey,"address"))

    if len(email)>0:
      wallet_appli=self.nfluent_wallet_url(address,self.network,domain_appli)

      if send_mail(open_html_file(mail_content,{
        "wallet_address":address,
        "mini_wallet":wallet_appli,
        "url_wallet":self.getExplorer(address),
        "url_explorer":self.getExplorer(address),
        "words":words,
        "qrcode":"cid:qrcode",
        "access_code":get_access_code_from_email(address)
      },domain_appli=domain_appli),email,subject=subject):
        histo.add_email(email,address,self.network)

    return _u, "",words,""


  def get_keys(self,qrcode_scale=0,with_balance=False,with_account=False):
    """
    Récupération des clés
    :param qrcode_scale:
    :param with_balance:
    :return:
    """

    rc=[]
    log("Lecture des clés "+str(listdir(POLYGON_KEY_DIR)))
    for fname in listdir(POLYGON_KEY_DIR):
      #log("Lecture de "+fname)

      if fname.endswith("admin.secret"): #or f.endswith(".json"):
        f=open(POLYGON_KEY_DIR+fname,"r")
        key = f.read().replace("\n","")
        _u = self.w3.eth.account.from_key(key)

        rc.append({
          "name":fname.replace(".secret",""),
          "pubkey":_u.address,
          "qrcode": get_qrcode(_u.address,qrcode_scale) if qrcode_scale>0 else "",
          "explorer":self.getExplorer(_u.address,"address"),
          "balance":self.balance(_u.address) if with_balance else 0,
          "unity":"MATIC",
          "account":_u if with_account else None
        })


    return rc

  def get_collections(self, addr):
    return []

  def toAccount(self, addr):
    for k in self.get_keys(with_account=True):
      if k["pubkey"]==addr or k["name"]==addr: return k["account"]


