import datetime
from os import listdir

import requests
from eth_account import Account
from solcx import compile_source, install_solc
from web3.contract import Contract
from web3.middleware import geth_poa_middleware

from flaskr.Keys import Key
from flaskr.NFT import NFT
from flaskr.NFluentAccount import NfluentAccount
from flaskr.Network import Network
from flaskr.Storage import Storage

from flaskr.Tools import log, get_qrcode, send_mail, open_html_file, get_access_code_from_email, returnError
from flaskr.dao import DAO
from web3 import Web3, HTTPProvider

from flaskr.secret import POLYGON_SCAN_API_KEY

POLYGON_DIR="./Polygon/"
POLYGON_KEY_DIR=POLYGON_DIR+"Keys/"
install_solc(version='latest')


POLYGON_BANK_ACCOUNT={
  "address":"0x52D011E89EAAefd089FF7C6200C014Dd421120D7",
  "privateKey":"0x556fd1f1c080b2dec397db6f58cf30e22c06efeda3e15b2749f65f202b61f3ce"
}

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


  def isEtherAddress(self,addr):
    if type(addr)==int: addr=hex(addr)
    if not addr.startswith("0x"): return False
    if not len(addr)==42: return False
    return True

  def send_transaction(self,method,_account:Key) -> str:
    gas_needed=method.estimate_gas({"from":_account.address})
    transac=method.build_transaction({"from":_account.address,"gas":gas_needed,"nonce":self.w3.eth.getTransactionCount(_account.address)})
    sign_transac=self.w3.eth.account.sign_transaction(transac,private_key=_account.secret_key)
    tx_hash =self.w3.eth.sendRawTransaction(sign_transac.rawTransaction)
    self.w3.eth.waitForTransactionReceipt(tx_hash)
    log("Execution de la transaction : "+self.getExplorer(tx_hash.hex(),"tx"))

    return tx_hash.hex()


  def init_contract_interface(self,price=0):
    src=open(POLYGON_DIR+"Master/contracts/NFTCollection.sol","r").read()
    src=src.replace("PRICE = 0 ether","PRICE = "+str(price)+" ether")
    libs=["@openzeppelin="+POLYGON_DIR+"Master/node_modules/@openzeppelin"]
    contract_id, contract_interface = compile_source(src,output_values=["abi","bin"],import_remappings=libs).popitem()
    return contract_interface


  def deploy_contract(self,_miner:Key,contract_interface,name,symbol,uri) -> Contract :
    abi=contract_interface['abi']
    bytecode=contract_interface['bin']
    constructor_contract=self.w3.eth.contract(abi=abi,bytecode=bytecode).constructor(uri,name,symbol)
    _tx=self.send_transaction(constructor_contract,_miner)

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
      message=result.json()["message"]
      if message=="NOTOK":
        raise RuntimeError(result.json()["result"])
      else:
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


  def get_metadata(self,uri,timeout=5):
    """
    voir https://docs.opensea.io/docs/metadata-standards
    :param uri:
    :param timeout:
    :return:
    """
    if uri is None:return None

    if not uri in self.metadata_cache:
      try:
        metadata=requests.get(uri,timeout=timeout)
        if metadata.status_code==200:
          self.metadata_cache[uri]=metadata.json()
          return self.metadata_cache[uri]
        else:
          log("Impossible de lire "+uri+", errorcode="+str(metadata.status_code))
      except:
        log("Impossible de lire "+uri+" dans le delai")

    return None



  def get_nft(self,addr,metadata_timeout=2,attr=True):
    contract_addr=addr.split("-")[0]
    log("Récupération du contract "+self.getExplorer(contract_addr))

    if not self.abi: self.abi=self.init_contract_interface()["abi"]
    _contract=self.w3.eth.contract(address=self.w3.toChecksumAddress(contract_addr),abi=self.abi)

    metadata=self.get_metadata(_contract.functions.baseTokenURI().call(),timeout=metadata_timeout)
    owner=_contract.functions.ownerOf(0).call()  #0 designe le seul tokenId du smartcontrat
    quantity=_contract.functions.totalSupply().call()
    miner=_contract.functions.owner().call()
    symbol=_contract.functions.symbol().call()
    _nft=NFT(name=metadata["name"] if metadata else "",
             owner=owner,
             miner=miner,
             symbol=symbol,
             description=metadata["description"]  if metadata else "",
             visual=metadata["image"]  if metadata else "",
             attributes=metadata["attributes"]  if metadata else "",
             address=addr,
             creators=metadata["creators"] if metadata and "creators" in metadata else [],
             marketplace=metadata["marketplace"] if metadata and "marketplace" in metadata else {"price":0,"quantity":quantity},
             royalties=100,
             collection=metadata["collection"] if metadata else None
             )
    return _nft


  def toEtherAddress(self,addr):
    if type(addr)==int: addr=hex(addr)
    try:
      addr=self.w3.toChecksumAddress(addr.lower())
    except:
      addr=None
    return addr


  def get_account(self,addr) -> NfluentAccount:
    if addr is None: return None
    if type(addr)==int: addr=hex(addr)
    if addr.startswith("0x"): addr=self.toEtherAddress(addr)

    return NfluentAccount(address=addr,balance=self.w3.eth.get_balance(addr),unity="MATIC",explorer=self.getExplorer(addr,"address"))


  # def get_nfts_old(self,addr,limit=2000,with_attr=False,offset=0,with_collection=False,metadata_timeout=5):
  #   transactions = self.w3.eth.get_transaction_count(addr)
  #
  #   # Iterate through all transactions and their associated events
  #   rc=[]
  #   for i in range(transactions):
  #     tx_hash = self.w3.eth.get_tra(addr, i)
  #     t = self.w3.eth.getTransactionReceipt(tx_hash)
  #
  #     for event in t['logs']:
  #         if event['address'] in "":
  #           log("Transaction prise en compte : "+t["explorer"])
  #           if with_attr:
  #             _nft=self.get_nft(t["contractAddress"]+"-"+t['tokenID'],metadata_timeout=metadata_timeout)
  #           else:
  #             _nft=NFT(name=t["tokenName"],miner=t["to"],owner=t["to"],address=t["contractAddress"],dtCreate=t["timeStamp"])
  #           _nft.symbol=t["tokenSymbol"]
  #           if len(rc)<limit and not _nft.address in [x.address for x in rc]:
  #             rc.append(_nft)
  #
  #   return rc


  def find_all_contract_for(self,addr):
    addr=self.toAccount(addr).address
    transactions=self.polygon_scan(addr,action="tokennfttx")
    rc=[]
    for t in transactions:
      if not t["contractAddress"] in rc: rc.append(t["contractAddress"])
    return rc

  def get_nfts(self,addr,limit=2000,with_attr=False,offset=0,with_collection=False,metadata_timeout=5):
    rc=[]
    addr=self.toAccount(addr).address
    abi=self.init_contract_interface()["abi"]
    l_contracts=self.find_all_contract_for(addr)
    for contract_addr in l_contracts:
      try:
        nft_addr=self.w3.toChecksumAddress(contract_addr)
        contrat=self.w3.eth.contract(address=nft_addr, abi=abi)
        balance = contrat.functions.balanceOf(addr).call()
        if balance==1:
          if with_attr:
            rc.append(self.get_nft(nft_addr))
          else:
            rc.append(NFT(address=nft_addr,marketplace={"quantity":balance},owner=addr))
          if len(rc)==limit: break
      except:
        log("Probleme technique de lecture des NFTs")
    return rc




  # def get_nfts(self,addr,limit=2000,with_attr=False,offset=0,with_collection=False,metadata_timeout=5):
  #   rc=[]
  #   _user=self.get_account(addr=addr)
  #   if _user:
  #     transactions=self.polygon_scan(_user.address,action="tokennfttx")
  #     for t in transactions:
  #       tt=self.w3.eth.getTransactionReceipt(t["hash"])
  #       if int(t["to"],16)==int(addr,16) and int(t["from"],16)==0:
  #         log("Transaction prise en compte : "+t["explorer"])
  #         if with_attr:
  #           _nft=self.get_nft(t["contractAddress"]+"-"+t['tokenID'],metadata_timeout=metadata_timeout)
  #         else:
  #            _nft=NFT(name=t["tokenName"],miner=t["to"],owner=t["to"],address=t["contractAddress"],dtCreate=t["timeStamp"])
  #         _nft.symbol=t["tokenSymbol"]
  #         if len(rc)<limit and not _nft.address in [x.address for x in rc]:
  #           rc.append(_nft)
  #       else:
  #         log("Transaction rejetée "+t["explorer"])
  #
  #   return rc



  def compile(self,miner:Key,title,symbol,uri,price=0) -> Contract:
    """
    deploiement voir https://docs.moonbeam.network/builders/build/eth-api/libraries/web3py/
    :param miner:
    :param title:
    :param symbol:
    :param uri:
    :return:
    """
    contract_interface = self.init_contract_interface(price)
    self.abi=contract_interface["abi"]
    contract = self.deploy_contract(miner,contract_interface,title,symbol,uri)
    return contract



  def opensea_metadata(self,title="",description="",visual="",
                       properties=[],animation_url="",collection:dict={},
                       price=0,quantity=1,creators=[],tags="",
                       from_nft:NFT=None):
    """
    voir https://docs.opensea.io/docs/metadata-standards
    :return:
    """
    if from_nft is None:
      attributes=[]
      if type(properties)==dict:
        for k in properties.keys():
          attributes.append({"trait_types":k,"value":properties[k]})
      else:
        attributes=properties
    else:
      description=from_nft.description
      animation_url=from_nft.visual
      attributes=from_nft.attributes
      visual=from_nft.visual
      tags=from_nft.tags
      price=from_nft.marketplace["price"]
      quantity=from_nft.marketplace["quantity"]
      collection=from_nft.collection
      creators=from_nft.creators

    rc={
      "description":description,
      "animation_url":animation_url,
      "external_url": "",
      "image": visual,
      "name": title,
      "tags":tags,
      "attributes": attributes,
      "collection":collection,
      "marketplace":{"price":price,"quantity":quantity},
      "creators":creators
    }
    #Collection et marketplace ne font pas partie de la norme proposé par solana
    return rc


  def mint(self, miner:Key, title,description="", collection={}, properties: list=[],storage:Storage=None,
           files=[], quantity=1, royalties=0, visual="", tags="",creators=[],
           domain_server="",_metadata=None,price=0,symbol="NFluenToken"):
    #properties["tag"]=tags
    #properties["royalties"]=royalties
    if _metadata is None:
      _metadata=self.opensea_metadata(title,description,visual,properties,collection=collection["id"],creators=creators,tags=tags)

    cid=storage.add(_metadata)
    contract=self.compile(miner,title,symbol,cid["url"],price)
    tx=self.send_transaction(contract.functions.mintNFTs(quantity),miner)
    self.approve(contract.address,miner.address,miner)

    if tx is None: return returnError("Erreur de minage")
    log("NFT disponible à l'adresse : "+self.getExplorer(contract.address,"token"))
    rc={
      "error":"",
      "tx":tx,
      "result":{"transaction":tx,"mint":contract.address},
      "balance":0,
      "link_mint":self.getExplorer(contract.address,"token"),
      "link_transaction":self.getExplorer(tx),
      "out":"",
      "cost":0,
      "unity":"MATIC",
      "command":"insert"
    }
    return rc


  def approve(self,nft_addr:str,operator:str,miner:Key):
    """
    voir https://docs.openzeppelin.com/contracts/3.x/api/token/erc721#IERC721-setApprovalForAll-address-bool-
    :param nft_addr:
    :param miner:
    :param operator: address recevant la possibilité de transfert
    :return:
    """
    addr=self.w3.toChecksumAddress(nft_addr)
    if not self.abi: self.abi=self.init_contract_interface()["abi"]
    _contract=self.w3.eth.contract(address=addr,abi=self.abi)
    #voir https://docs.openzeppelin.com/contracts/3.x/api/token/erc721#IERC721-approve-address-uint256-
    if operator!=miner.address:
      tx=self.send_transaction(_contract.functions.approve(operator,0),miner)
    return True


  def transfer(self,nft_addr:str,miner:Key,new_owner:str):
    """
    voir https://eips.ethereum.org/EIPS/eip-721#implementations
    https://docs.openzeppelin.com/contracts/2.x/api/token/erc721#ERC721-transferFrom-address-address-uint256-
    :param nft_addr:
    :param new_owner:
    :return:
    """

    if not self.abi: self.abi=self.init_contract_interface()["abi"]
    contract=self.w3.eth.contract(address=self.w3.toChecksumAddress(nft_addr),abi=self.abi)

    owner=contract.functions.ownerOf(0).call()
    if owner!=miner.address:
      #raise RuntimeError("Probleme de propriétaire pour le transfert")
      log("Le propriétaire n'est pas le mineur")
    rc= self.send_transaction(contract.functions.transferFrom(miner.address,new_owner,0),miner)
    return rc


  def balance(self,account):
    return self.w3.eth.get_balance(account)/1e18



  def add_key(self,key,filename=""):
    if len(filename)==0:filename=hex("str")
    if not filename.endswith(".secret"):filename=filename+".secret"
    with open(POLYGON_KEY_DIR+filename,"w") as f:
      f.writelines(key[1])
    return True


  def getExplorer(self,address:str="",type_param="address") -> str:
    return "https://"+("mumbai." if "devnet" in self.network else "")+"polygonscan.com/"+type_param+"/"+address


  def getNFTExplorer(self,address:str,type_param="assets"):
    return "https://"+\
           ("testnets." if "devnet" in self.network else "")+\
           ".opensea.io/"+ type_param + "/" + \
           ("mumbai" if "devnet" in self.network else "")+ \
           "/"+address




  def create_account(self,email="",seed="",domain_appli="",
                         subject="Votre compte Polygon est disponible",histo:DAO=None,
                     mail_new_wallet="",mail_existing_wallet="",send_qrcode_with_mail=True,send_real_email=True) -> Key:
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
        send_mail(open_html_file(mail_existing_wallet,{
          "wallet_address":pubkey,
          "mini_wallet":self.nfluent_wallet_url(pubkey,domain_appli),
          "url_explorer":self.getExplorer(pubkey)
        },domain_appli=domain_appli),email,subject=subject)
        _u.address=pubkey
        return _u,None,None,None

    words=""
    secret_key=""
    if len(seed) == 0:
      _u:Account=self.w3.eth.account.create()
    else:
      _u=self.w3.eth.account.create_with_mnemonic(passphrase=seed)
      words=seed

    pubkey = _u.address
    secret_key=self.w3.toHex(_u.privateKey)

    log("Création du compte "+self.getExplorer(pubkey,"address"))

    if len(email)>0:
      wallet_appli=self.nfluent_wallet_url(pubkey,domain_appli)

      if send_mail(open_html_file(mail_new_wallet,{
        "wallet_address":pubkey,
        "mini_wallet":wallet_appli,
        "url_wallet":self.getExplorer(pubkey),
        "url_explorer":self.getExplorer(pubkey),
        "words":words,
        "qrcode":"cid:qrcode",
        "access_code":get_access_code_from_email(pubkey)
      },domain_appli=domain_appli),email,subject=subject):
        histo.add_email(email,pubkey,self.network)

    return Key(secret_key=secret_key,name=email.split("@")[0],seed=words,network="polygon",address=pubkey)

  def faucet(self,addr:str,amount:float,from_account:str="bank"):
    bank=self.get_account(from_account)
    if bank["amount"]>amount:
      nonce = self.w3.eth.getTransactionCount(POLYGON_BANK_ACCOUNT["address"])
      tx = {
        'nonce': nonce,
        'to': addr,
        'value': self.w3.toWei(amount, 'ether'),
        'gas': 200000,
        'gasPrice': self.w3.eth.gasPrice
      }
      signed_tx =self.w3.eth.account.sign_transaction(tx, POLYGON_BANK_ACCOUNT["privateKey"])
      tx_hash = self.w3.eth.sendRawTransaction(signed_tx.rawTransaction)
      return True
    else:
      log("Fonds insuffisants")
      return False

  def get_keys(self,qrcode_scale=0,with_balance=False,with_account=False,address=""):
    """
    Récupération des clés
    :param qrcode_scale:
    :param with_balance:
    :return:
    """

    rc=[]
    log("Lecture des clés "+str(",".join(listdir(POLYGON_KEY_DIR))))
    for fname in listdir(POLYGON_KEY_DIR):
      #log("Lecture de "+fname)

      if fname.endswith(".secret"): #or f.endswith(".json"):
        f=open(POLYGON_KEY_DIR+fname,"r",encoding="utf8")
        key = f.read().replace("\n","")
        _u = self.w3.eth.account.from_key(key)

        rc.append(Key(secret_key=_u.privateKey.hex(),
                      name=fname.replace(".secret",""),
                      address=_u.address,
                      network="polygon"))

    return rc


  def get_collections(self, addr="",detail=False,filter_type="NFT"):
    nfts=self.get_nfts(addr,with_attr=True,with_collection=False,metadata_timeout=1)
    rc=[]
    for nft in nfts:
      if nft.collection and nft.collection!={} and not nft.collection in rc:
        rc.append(nft.collection)
    return rc


  def get_balance(self,address):
    return self.get_account(address).balance


  def get_key_with_name(self,name="sophie"):
    for k in self.get_keys():
      if k.name==name:
        return k
    return None


  def toAccount(self, addr):
    """
    voir https://web3js.readthedocs.io/en/v1.2.11/web3-eth-accounts.html
    :param addr:
    :return:
    """
    if not addr.startswith("0x"):
      k=self.get_key_with_name(addr)
      if k is None: return None
      addr=k.address
    return self.w3.eth.contract(address=addr)


