import pickle
from os import listdir
from eth_account import Account
from solcx import compile_source, install_solc
from web3.contract import Contract
from web3.middleware import geth_poa_middleware

from Network import Network

from Tools import log, get_qrcode, send_mail, open_html_file, get_access_code_from_email
from ipfs import IPFS
from web3 import Web3, HTTPProvider

POLYGON_KEY_DIR="./Polygon/Keys/"
install_solc(version='latest')


class Polygon (Network):
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

    return tx_hash.hex()


  def deploy_contract(self,miner,contract_interface,name,symbol,uri) -> Contract :
    abi=contract_interface['abi']
    bytecode=contract_interface['bin']
    _miner=self.toAccount(miner)
    constructor_contract=self.w3.eth.contract(abi=abi,bytecode=bytecode).constructor(uri,name,symbol)
    _tx=self.send_transaction(constructor_contract,miner)

    addr=self.w3.eth.get_transaction_receipt(_tx)['contractAddress']
    _contract=self.w3.eth.contract(address=addr,abi=abi)
    log("contract sur "+self.getExplorer(addr)+" deployé avec les fonctions "+str(_contract.functions.__dict__.keys()))

    return _contract


  def get_transactions(self,address,history_size=100):
    """This function takes three inputs, a starting block number, ending block number
    and an Ethereum address. The function loops over the transactions in each block and
    checks if the address in the to field matches the one we set in the blockchain_address.
    Additionally, it will write the found transactions to a pickle file for quickly serializing and de-serializing
    a Python object."""

    # request the latest block number
    ending_blocknumber = self.w3.eth.blockNumber

    # latest block number minus 100 blocks
    starting_blocknumber = ending_blocknumber - history_size

    # create an empty dictionary we will add transaction data to
    tx_dictionary = {}

    rc=[]
    for x in range(starting_blocknumber, ending_blocknumber):
      block = self.w3.eth.getBlock(x, True)
      for transaction in block.transactions:
        if transaction['to'] == address or transaction['from'] == address:
            rc.append(transaction)

    print(f"Finished searching blocks {start} through {end} and found {len(tx_dictionary)} transactions")





  def get_nfts(self,_user,limit=2000,with_attr=False,offset=0,with_collection=False):
    transactions=self.get_transactions(_user.address,limit)
    for t in transactions:
      pass



  def compile(self,miner:str,title,symbol,uri) -> Contract:
    """
    deploiement voir https://docs.moonbeam.network/builders/build/eth-api/libraries/web3py/
    :param miner:
    :param title:
    :param symbol:
    :param uri:
    :return:
    """
    src=open("./Polygon/Master/contracts/NFTCollection.sol","r").read()
    libs=["@openzeppelin=./Polygon/Master/node_modules/@openzeppelin"]
    contract_id, contract_interface = compile_source(src,output_values=["abi","bin"],import_remappings=libs).popitem()
    contract = self.deploy_contract(miner,contract_interface,title,symbol,uri)
    return contract



  def opensea_metadata(self,title,description,visual,properties,animation_url=""):
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
      "external_url": "https://openseacreatures.io/3",
      "image": visual,
      "name": title,
      "attributes": attributes
    }
    return rc


  def mint(self, miner, title,description, collection, properties: dict,ipfs:IPFS,files=[], quantity=1, royalties=0, visual="", tags=""):
    #properties["tag"]=tags
    #properties["royalties"]=royalties
    cid=ipfs.add(self.opensea_metadata(title,description,visual,properties))
    contract=self.compile(miner,title,"symbol",cid["url"])
    rc=self.send_transaction(contract.functions.mintNFTs(1),miner)
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
                         subject="Votre compte Polygon est disponible",mail_content="mail_new_account"):
    """
    :param fund:
    :param name:
    :param seed_phrase:
    :return: Account, PEM,words,qrcode
    """
    log("Création d'un nouveau compte sur "+self.network)

    if len(seed) == 0:
      _u:Account=self.w3.eth.account.create()
      address = _u.address
      secret_key=_u.key
    else:
      _u=self.w3.eth.account.create_with_mnemonic(passphrase=seed)
      qrcode=""
      secret_key=_u.key
      pubkey = _u.address
      words=seed
      _u.secret_key=secret_key.hex()

    log("Création du compte "+self.getExplorer(pubkey,"address"))

    if len(email)>0:
      wallet_appli=self.nfluent_wallet_url(address,self.network,domain_appli)

      send_mail(open_html_file(mail_content,{
        "wallet_address":address,
        "mini_wallet":wallet_appli,
        "url_wallet":"https://wallet.elrond.com" if "mainnet" in self.network else "https://devnet-wallet.elrond.com",
        "url_explorer":("https://explorer.elrond.com" if "mainnet" in self.network else "https://devnet-explorer.elrond.com") +"/accounts/"+address,
        "words":words,
        "qrcode":"cid:qrcode",
        "access_code":get_access_code_from_email(address)
      },domain_appli=domain_appli),email,subject=subject)

    return _u, "",words,""


  def get_keys(self,qrcode_scale=0,with_balance=False,with_account=False):
    """
    Récupération des clés
    :param qrcode_scale:
    :param with_balance:
    :return:
    """

    rc=[]
    for fname in listdir(POLYGON_KEY_DIR):
      log("Lecture de "+fname)

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


