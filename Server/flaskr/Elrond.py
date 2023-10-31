import base64
import io
from os.path import exists
from pathlib import Path
from typing import Optional

import requests
from multiversx_sdk_core import Transaction, Address, TransactionPayload, TokenPayment
from multiversx_sdk_core.transaction_builders import DefaultTransactionBuildersConfiguration, EGLDTransferBuilder, \
  ESDTTransferBuilder
from multiversx_sdk_network_providers.accounts import AccountOnNetwork
from multiversx_sdk_network_providers.network_config import NetworkConfig
from multiversx_sdk_network_providers.resources import SimulateResponse
from multiversx_sdk_wallet import UserPEM, UserSigner, UserSecretKey, Mnemonic,UserWallet
from multiversx_sdk_wallet.core import derive_keys
from multiversx_sdk_network_providers import ProxyNetworkProvider
from multiversx_sdk_wallet.user_wallet import UserWalletKind

from flaskr.Keys import Key
from flaskr.NFluentAccount import NfluentAccount
from flaskr.Network import Network
from flaskr.Storage import Storage

from flaskr.dao import DAO
import json
import time
from os import listdir

from time import sleep
import pyqrcode
from flaskr.Tools import hex_to_str, now, get_access_code_from_email, int_to_hex, str_to_hex, log, api, \
  send_mail, open_html_file, strip_accents, returnError, decrypt, extract_title_from_html, get_hash, extract_from_dict, \
  smart
from flaskr.NFT import NFT
import textwrap

RESULT_SECTION="smartContractResults"
LIMIT_GAS=200000000
PRICE_FOR_STANDARD_NFT=0.05

ELROND_KEY_DIR="./Elrond/PEM/"      #Le repertoire de travail etant server

#voir https://docs.multiversx.com/tokens/nft-tokens/
#voir https://docs.multiversx.com/tokens/nft-tokens/#roles
DEFAULT_OPTION_FOR_ELROND_COLLECTION="canFreeze,canWipe,canPause,canTransferNFTCreateRole,canChangeOwner,canUpgrade,canAddSpecialRoles"
DEFAULT_ROLE_FOR_NFT="ESDTRoleNFTCreate" #,ESDTRoleNFTBurn,ESDTRoleNFTUpdateAttributes,ESDTRoleNFTAddURI,ESDTTransferRole"
DEFAULT_ROLE_FOR_SFT="ESDTRoleNFTCreate,ESDTRoleNFTAddQuantity" #,ESDTRoleNFTBurn,ESDTRoleNFTUpdateAttributes,ESDTRoleNFTAddURI,ESDTTransferRole"


NETWORKS={
  "localnet":{
    "unity":"xEgld",
    "identifier":"TFE-116a67",
    "faucet":"https://devnet-wallet.multiversx.com",
    "proxy":"http://192.168.1.62:7950",
    "explorer":"http://192.168.1.62:7950/transactions",
    "gallery":"https://devnet.xspotlight.com",
    "wallet":"https://devnet-wallet.multiversx.com",
    "nft":"erd1qqqqqqqqqqqqqqqpqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqzllls8a5w6u",
    "esdt":"erd1qqqqqqqqqqqqqqqpqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqzllls8a5w6u",
    "shard": 1
  },

  "testnet":{
    "unity":"xEgld",
    "faucet":"https://r3d4.fr/elrond/testnet/index.php",
    "proxy":"https://testnet-api.multiversx.com",
    "explorer":"https://testnet-explorer.multiversx.com",
    "wallet":"http://testnet-wallet.multiversx.com",
    "nft":"erd1qqqqqqqqqqqqqqqpqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqzllls8a5w6u",
    "esdt":"erd1qqqqqqqqqqqqqqqpqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqzllls8a5w6u",
    "shard":0
  },

  #erd1qqqqqqqqqqqqqpgqkwfvpkaf6vnn89508l0gdcx26vpu8eq5d8ssz3lhlf
  "devnet":{
    "unity":"xEgld",
    "identifier":"TFE-116a67",
    "faucet":"https://devnet-wallet.multiversx.com",
    "proxy":"https://devnet-api.multiversx.com",
    "explorer":"https://devnet-explorer.multiversx.com",
    "gallery":"https://devnet.xspotlight.com",
    "wallet":"https://devnet-wallet.multiversx.com",
    "nft":"erd1qqqqqqqqqqqqqqqpqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqzllls8a5w6u",
    "esdt":"erd1qqqqqqqqqqqqqqqpqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqzllls8a5w6u",
    "shard": 1
  },

 "devnet2":{
    "unity":"xEgld",
    "identifier":"TFE-116a67",
    "faucet":"https://devnet2-wallet.multiversx.com",
    "proxy":"https://devnet2-api.multiversx.com",
    "explorer":"https://devnet2-explorer.multiversx.com",
    "gallery":"https://devnet2.xspotlight.com",
    "wallet":"https://devnet2-wallet.multiversx.com",
    "nft":"erd1qqqqqqqqqqqqqqqpqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqzllls8a5w6u",
   "esdt":"erd1qqqqqqqqqqqqqqqpqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqzllls8a5w6u",
    "shard": 1
  },

  "mainnet":{
    "unity":"Egld",
    "identifier":"",
    "faucet":"",
    "proxy":"https://api.multiversx.com",
    "explorer":"https://explorer.multiversx.com",
    "wallet":"https://wallet.multiversx.com",
    "gallery":"https://xspotlight.com",
    "nft":"erd1qqqqqqqqqqqqqqqpqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqzllls8a5w6u",
    "esdt":"erd1qqqqqqqqqqqqqqqpqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqzllls8a5w6u",
    "shard": 1
  }
}


class Elrond(Network):

  cost_per_byte=1500
  persist_per_byte=1000
  store_per_byte=10000

  def __init__(self,network="elrond-devnet"):
    super().__init__(network)
    self._proxy=ProxyNetworkProvider(NETWORKS[self.network_type]["proxy"])
    self.transactions=[]
    self.init_idx_collection(self.network_type)


  def save_data_to_account(self,miner:Key,data:dict):
    """
    voir https://docs.multiversx.com/developers/account-storage
    :param data:
    :return:
    """
    transac_data="SaveKeyValue"
    gas_limit=100000+50000
    for k in data.keys():
      value=data[k]
      data_to_add="@"+str_to_hex(k,False)+"@"+str_to_hex(value,False)
      transac_data=transac_data+data_to_add
      gas_limit=gas_limit+self.cost_per_byte+len(data_to_add)+self.persist_per_byte*len(k)+self.persist_per_byte*len(value)+self.store_per_byte*len(value)

    return self.send_transaction(_sender=miner,_receiver=miner.address,_sign=miner,data=transac_data,value=0,gas_limit=gas_limit*2)

  def get_data_from_account(self,address:str) -> dict:
    """
    voir
    :param address:
    :return:
    """
    url=self._proxy.url.replace("api","gateway")+"/address/"+address+"/keys"
    log("Ouverture de "+url)
    result=requests.get(url)
    data=None
    encrypted_data:dict=result.json() if result.status_code==200 else None
    if encrypted_data:
      data=dict()
      for k in encrypted_data["data"]["pairs"].keys():
        data[hex_to_str(k)]=hex_to_str(encrypted_data["data"]["pairs"][k])

    return data





  def get_unity(self):
    return "egld"

  def toAddress(self,private_key:str):
    return private_key[0:16]


  def canMint(self,nft_to_check:NFT,dest:str="",miner:str=""):
    """
    Vérifie si un NFT a déjà été miné ou pas
    TODO: fonction à coder
    :param nft_to_check:
    :return:
    """
    if nft_to_check.address!="" and not nft_to_check.address.startswith("db_"): return False
    if dest!="" and not "@" in dest:
      col=nft_to_check.collection["id"]
      nfts=self.get_nfts(self.toAccount(dest),with_attr=False)
      occurences=dict() #Contient le nombre de fois ou le nft a été miné
      for nft in nfts:
        if nft.collection:
          occurences[col]=occurences[col]+1 if col in occurences.keys() else 1

    return nft_to_check.balance[miner]>0


  def find_alias(self,addr,keys=[]):
    if len(keys)==0:keys=self.get_keys()
    for k in keys:
      if k["address"]==addr:
        return k["name"]

    result=api(self._proxy.url+"/accounts/"+addr)

    if "username" in result and len(result["username"])>0:
      keys.append({"address":addr,"name":result["username"]})
      return result["username"]

    keys.append({"address":addr,"name":addr})
    return addr




  def get_transactions_from_collection(self,address,size=300):
    result=api(self._proxy.url.replace("gateway","api")+"/collections/"+address+"/transactions?status=success&from=0&size="+str(size))
    if result:
      for t in result:
        sender=t["sender"]
        value=int(t["value"])
        method=t["action"]["name"]
        collection=address
        token=""
        receiver=t["receiver"]
        if method=="transfer":
          receiver=t["action"]["arguments"]["receiver"]
          token=t["action"]["arguments"]["transfers"][0]["identifier"]
          method="Transfert"

        if method=="ESDTNFTCreate":
          token=""
          method="Minage"

        self.transactions.append({
          "from":sender,
          "to":receiver,
          "id":t["txHash"],
          "cost":int(t["fee"])/1e18,
          "ts":t["timestamp"],
          "method":method,
          "token":token,
          "collection":collection,
          "value":value
        })




  def get_transactions(self,address,limit=1000,size=20,profondeur=0,profondeur_max=3,methods=[],exclude_addresses=[]):
    """
    voir
    :return:
    """
    result=api(self._proxy.url+"/accounts/"+address+"/transactions?status=success&from=0&size="+str(size)) if len(self.transactions)<limit else None
    if result:
      time.sleep(1)
      for t in result:
        sender=t["sender"]
        receiver=t["receiver"]
        id=t["txHash"]
        value=int(t["value"])
        method=""
        token=""
        collection=""
        if "data" in t:
          data=str(base64.b64decode(t["data"])).replace("b\'","").replace("b\'","").split("@")
          method=data[0]
          if method=="ESDTNFTCreate":
            collection=hex_to_str(data[1])

          if method=="ESDTTransfer":
            token=hex_to_str(data[1])

          if method=="ESDTNFTTransfer":
            try:
              data[4]=data[4].replace("\'","")
              addr=data[4] if len(data[4]) % 2==0 else "0"+data[4]
              receiver=self._proxy.get_account(address=addr).public_key.to_address("erd").bech32()
            except:
              pass

            collection=hex_to_str(data[1])
            nonce=data[2]
            token=collection+"-"+nonce

        obj={
          "from":sender,
          "to":receiver,
          "id":id,
          "ts":t["timestamp"],
          "method":method,
          "token":token,
          "collection":collection,
          "value":value
        }

        if not obj in self.transactions and len(methods)==0 or method in methods and len(self.transactions)<limit:
          self.transactions.append(obj)
          log(str(int(100*len(self.transactions)/limit))+"% terminés")

        if profondeur<=profondeur_max:
          new_address=sender if sender!=address else receiver
          if not new_address in exclude_addresses and new_address!=address:
            exclude_addresses.append(new_address)
            self.get_transactions(new_address,limit,size,profondeur+1,profondeur_max,methods,exclude_addresses)

      return self.transactions





  def getExplorer(self, tx="", _type="transactions") -> str:
    if type(tx)==Address:
      _type="address"
      tx=tx.bech32()
    url = NETWORKS[self.network_type]["explorer"] + "/" + _type + "/"
    if len(tx)>0:url=url+tx
    url=url.replace("api","explorer")
    return url

  def getGallery(self, address:str,section="") -> str:
    url = NETWORKS[self.network_type]["gallery"] + "/" + section+address
    return url

  def getWallet(self,addr=""):
    return NETWORKS[self.network_type]["wallet"] + "/" + addr



  def send_transaction(self,transaction,_sign: Key | str=None,
                        timeout=120,simulation=False,delay_between_check=3.0) -> dict:
    """
    Envoi d'une transaction signée
    voir https://docs.multiversx.com/sdk-and-tools/sdk-py/sdk-py-cookbook#egld--esdt-transfers
    :param _sender:
    :param _receiver:
    :param _sign:
    :param value:
    :param data:
    :return:
    """
    if type(transaction)==dict:
      sender=Address.from_bech32(transaction["sender"])
      receiver=Address.from_bech32(transaction["receiver"])
      _transaction=Transaction(transaction["chainID"],
                              sender,receiver,
                              transaction["gasLimit"],
                              transaction["gasPrice"],
                              transaction["nonce"],
                              transaction["value"],
                              TransactionPayload.from_encoded_str(transaction["data"]),
                              transaction["version"])

      if "signature" in transaction and transaction["signature"]!="":
        _transaction.signature=bytes.fromhex(transaction["signature"])

      transaction=_transaction

    if transaction.signature is None or transaction.signature==bytes(0):
      #Si la transaction n'est pas signé elle peut l'être par le système
      log("On signe la transaction avec le compte " + self.getExplorer(_sign.address,"address"))
      _signer=UserSigner(UserSecretKey(bytes.fromhex(_sign.secret_key)))
      transaction.signature=_signer.sign(transaction)

    try:
      if not simulation:
        hash = self._proxy.send_transaction(transaction)
        log("Execution de la transaction " + self.getExplorer(hash))

        start=now()
        d=None
        while now()-start<timeout:
          sleep(delay_between_check)
          d=self._proxy.get_transaction(hash)
          if d.status.status=="success":break

        d=d.to_dictionary()

      else:
        r = self._proxy.simulate_transaction(transaction)
        hash=r.raw["result"]["hash"]

      d["explorer"]=self.getExplorer(hash)
      d["error"]=d["status"] if not d["status"]=="success" else ""
      d["results"]=dict()
      fields_to_translate=["issue","signalError","issueNonFungible","issueSemiFungible"]
      results=dict()
      if "logs" in d:
        for e in d["logs"]["events"]:
         results[e["identifier"]]=[hex_to_str(x) for x in e["topics"]] if e["identifier"] in fields_to_translate else e["topics"]

      if "smartContractResults" in d:
        for e in d["smartContractResults"]:
          k=e["data"].split("@")[0]
          results[k]=e["data"].replace(k+"@","").split("@")


      d["results"]=results
      return d

    except Exception as inst:
      mess=str(inst.args).split(":")
      mess=":".join(mess[2:]) if len(mess)>2 else ":".join(mess)
      mess=mess.strip()
      log("Exception d'execution de la requete " + mess)
      if mess.startswith("{"):
        mess=(mess.split("}")[0]+"}").replace("'","\"").replace("None","\"\"")
        return {"error":json.loads(mess),"status":"error","hash":""}

      return {"error":mess,"status":"error","hash":""}




  def get_collections(self, addr:str, detail:bool=True, type_collection="", special_role="",limit=50,withSupply=False):
    """
    récupération des collections voir : https://devnet-api.multiversx.com/#/accounts/AccountController_getAccountCollectionsWithRoles
    :param creator:
    :param fields:
    :return:
    """
    if type(addr)==Key: addr=addr.address
    if type(addr)==AccountOnNetwork: addr=self.find_key(addr).address
    if addr.startswith("erd"):
      owner=addr
      url=self._proxy.url+"/accounts/"+owner+"/roles/collections/?size="+str(limit)
      if len(type_collection)>0:
        if not "ESDT" in type_collection:type_collection= type_collection + "ESDT"
        url= url +"&type=" + type_collection

      if len(special_role)==0:
        url=url+"&owner="+owner
      else:
         for ask_role in special_role.split(","):
           assert ask_role in ["canAddUri","canTransferRole","canAddQuantity","canBurn","canCreate"],"Le rôle demandé "+ask_role+" n'existe pas"
           url=url+"&"+ask_role+"=true"

      result=api(url,"gateway=api")
      if not result is None:
        cols=result
      else:
        log("Bug: Impossible de récupérer les NFTs de "+addr)
        return []
    else:
      cols=self.find_collections(addr,limit=limit,_type="")
      #cols=cols+self.find_collections(addr,limit=limit,_type="SemiFungible")
    rc=[]
    if cols is None: return []

    for _col in cols:
      if not "id" in _col: _col["id"]=_col["collection"]
    #   if "role" in _col:
    #     if "roles" in _col["role"]:
    #       del _col["role"]["roles"]
    #
    #     if not "roles" in _col:
    #       _col["roles"]=[_col["role"]]
    #       del _col["role"]
    #
    #     if not "address" in _col["roles"][0]: _col["roles"][0]["address"]=_col["owner"]

      # exclude=False
      # if len(special_role)>0:
      #   for r in special_role.split(","):
      #     if not r in _col or not _col[r]:
      #       exclude=True
      #       break

      # if "roles" in _col:
      #   for role in _col["roles"]:
      #     if role["address"]==addr:
      #       for r in special_role.split(","):
      #         if not r in role or not role[r]:
      #           exclude=True
      #           break
      # else:
      #   if len(special_role)>0: exclude=True
      #

      if withSupply:
        if addr!="":
          balance=api(self._proxy.url+"/accounts/"+addr+"/nfts/count?collection="+_col["id"])
          _col["balances"]={addr:int(balance)}

      _col["link"]="https://"+("devnet." if "devnet" in self.network else "")+"inspire.art/collections/"+_col["id"]
      if len(type_collection)==0 or type_collection in _col["type"]:
        rc.append(_col)

    rc=sorted(rc,key=lambda x:x["timestamp"] if "timestamp" in x else 0,reverse=True)

    if detail:
      for item in rc:
        item["id"]=item["ticker"]
        item["options"]={
          "canFreeze":item["canFreeze"],
          "canTransfer":item["canTransfer"] if "canTransfer" in item else False,
          "canWipe":item["canWipe"],
          "canPause":item["canPause"],
          "canTranferNftCreateRole":item["canTransferNftCreateRole"]
        }

    return rc


  idx_collections=dict()
  n_cols=0
  def init_idx_collection(self,network:str,filename="./collections.json"):
    if not network in self.idx_collections:
      if exists(filename):
        with open(filename, "r") as f:
          self.idx_collections=json.load(f)

    if not network in self.idx_collections:
      self.idx_collections[network]=dict()
      step=1000
      offset=0
      self.n_cols=0
      while True:
        log("Indexation des collections de "+network+" de "+str(offset)+" à "+str(offset+step))
        cols=requests.get(self._proxy.url+"/collections?from="+str(offset)+"&size="+str(step)).json()
        for col in cols:
          if "name" in col:
            if not col["name"] in self.idx_collections[network]:self.idx_collections[network][col["name"]]=[]
            self.idx_collections[network][col["name"]].append(col["ticker"])
        self.n_cols=self.n_cols+len(cols)
        if len(cols)<step:
          break
        offset=offset+step

      with open(filename, "w") as f: json.dump(self.idx_collections, f)



      log("Initiailisation de l'index terminé")

  def find_collections(self, query:str,limit=5000,_type="") -> [dict]:
    """
    Récupère l'ensemble des collections
    voir https://devnet-api.multiversx.com/#/collections/CollectionController_getNftCollections
    :param query:
    :param limit:
    :return:
    """
    if _type!="":_type="&type="+_type+"ESDT"
    query=query.strip()

    tickers=[]
    if query!="" and not query.startswith("erd") and not "-" in query:
      query=query.lower()
      self.init_idx_collection(self.network_type)
      for k in self.idx_collections[self.network_type].keys():
        if query in k.lower(): tickers=tickers+self.idx_collections[self.network_type][k]
      if len(tickers)==0: return []
    else:
      if len(query.split("-"))==2:
        tickers=[query]
      else:
        limit=min(limit,100)    #on accepte de faire des recherche importante s'il y a un critère de recherche

    query_identifiers=""
    query_others="&sort=verifiedAndHolderCount&order=desc"
    query_size="size="+str(limit)
    if len(tickers)>0:
      query_identifiers="&identifiers="+",".join(tickers)
      query_others=""
      query_size="&from=0&size="+str(len(tickers))
      _type=""

    resp=requests.get(self._proxy.url+"/collections?"+query_size+_type+query_identifiers+query_others)
    if resp.status_code==200:
      cols=[]
      for col in resp.json():
        col["supply"]=col["nftCount"] if "nftCount" in col else 1
        col["label"]=col["name"]
        if query=="" or query in col["name"].lower() or query in col["ticker"].lower() or query in col["owner"].lower(): cols.append(col)

      return cols

    return []



  def get_collection(self,collection_id):
    rc=api(self._proxy.url+"/collections/"+collection_id,"gateway=api")
    if not rc is None:
      if "ticker" in rc:
        rc["id"]=rc["ticker"]
      else:
        rc["id"]=rc["collection"]

      # if not "roles" in rc:
      #   if "role" in rc:
      #     rc["roles"]=[rc["role"]]
      #   else:
      #     rc["roles"]=[{"address":rc["owner"]}]
      #     for k in ["canCreate",  "canBurn",  "canAddQuantity",  "canAddUri", "canUpdateAttributes"]:
      #       rc["roles"][0][k]=rc[k] if k in rc else False
      #
      #   rc["roles"][0]["address"]=rc["owner"]
      #
      # if "roles" in rc:
      #   for r in rc["roles"]:
      #     if "roles" in r: del r["roles"]

    return rc


  def format_offchain(self,_data) -> dict:
    keys=self.get_keys()
    for c in _data["creators"]:
      for k in keys:
        if k["name"]==c["address"]:
          c["address"]=k["address"]

    return {
      "properties":{
        "attributes":_data["attributes"],
        "description":_data["description"],
        "collection":_data["collection"],
        "creators":_data["properties"]["creators"]
      },
      "files":_data["properties"]["files"]
    }


  def transfer_money(self,token_id:str,miner:Key,to_addr:str,quantity=1,data="airdrop"):
    """
    voir https://docs.multiversx.com/sdk-and-tools/sdk-py/sdk-py-cookbook/#egld--esdt-transfers
    #tag transfer transferegld egld
    :param token_id:
    :param miner:
    :param to_addr:
    :param quantity:
    :return:
    """
    config = DefaultTransactionBuildersConfiguration(chain_id=self._proxy.get_network_config().chain_id)
    miner_address=self.toAccount(miner).address
    if token_id.lower()=="egld":
      payment = TokenPayment.egld_from_amount(str(quantity))
      builder = EGLDTransferBuilder(
        config=config,
        sender=miner_address,
        receiver=Address.from_bech32(to_addr),
        payment=payment,
        data=data,
        nonce=self.toAccount(miner).nonce #TODO : a revoir
      )
    else:
      payment = TokenPayment.fungible_from_amount(token_id,str(quantity),18)
      builder = ESDTTransferBuilder(
        config=config,
        sender=miner_address,
        receiver=Address.from_bech32(to_addr),
        payment=payment,
        nonce=self.toAccount(miner).nonce #TODO : a revoir
      )
    transaction=builder.build()
    return transaction





  def transfer(self,nft_addr:str,from_addr:str,to_addr:str,quantity=1):
    """
    Transfert d'un NFT
    voir https://docs.multiversx.com/tokens/nft-tokens/#transfers
    :param collection_id:
    :param nonce:
    :param _from:
    :param _to:
    :return:
    """
    # _to=self.toAccount(to_addr)
    # if _to is None:
    #   log("Destinataire inconnu")
    #   return False

    if from_addr==to_addr: return False

    log("Transfert de "+nft_addr+" de "+from_addr+" a "+to_addr)
    if len(nft_addr.split("-"))<2:
      log("Il s'agit d'un transfert de money")
      return self.transfer_money(nft_addr,from_addr,to_addr,quantity,"")

    collection_id,nonce=self.extract_from_tokenid(nft_addr)

    data = "ESDTNFTTransfer" \
           + "@" + str_to_hex(collection_id,False) \
           + "@" + nonce \
           + "@" + int_to_hex(quantity) \
           + "@" + self.toAccount(to_addr).address.hex()
    t = self.create_transaction(from_addr,data=data)
    return t


  def get_balance(self,addr,token_id="") -> int:
    acc=self.toAccount(addr)
    if token_id=="" or token_id=="egld":
      return acc.balance/(10**18)
    else:
      #voir https://api.multiversx.com
      url=self._proxy.url+"/accounts/"+acc.address.bech32()+"/tokens/"+token_id
      result= requests.get(url)
      balance=0
      if result.status_code==200:
        if "balance" in result.json():
          balance=int(result.json()["balance"])
          if balance>0:
            nb_decimals=result.json()["decimals"]
            return balance/(10**nb_decimals)

      url=self._proxy.url+"/collections/"+token_id+"/accounts/"
      result= requests.get(url)
      if result.status_code==200:
        for item in result.json():
          if item["address"]==acc.address.bech32(): return int(item["balance"])
      return 0




  def get_roles_for_collection(self,collection_id:str,account_address:str=""):
    """
    see https://devnet-api.multiversx.com
    :param nft_addr:
    :return:
    """
    if account_address=="":
      _c=self.get_collection(collection_id)
      result=_c["roles"]
    else:
      url=self._proxy.url+"/accounts/"+account_address+"/roles/collections/"+collection_id
      result= requests.get(url).json()
      if not "error" in result:
        result=result["role"]
      else:
        result= {"error":result["message"]}
    return result



  def analyse_collection_transaction(self,t,type_collection="NonFungible"):
    if RESULT_SECTION in t:
      log("Recherche du collection id")
      for result in t[RESULT_SECTION]:
        if len(result["data"].split("@"))>2:
          collection_id = hex_to_str(result["data"].split("@")[2])

          #voir les roles : https://docs.multiversx.com/tokens/nft-tokens/#roles
          roles_to_add="ESDTRoleNFTCreate,ESDTRoleNFTBurn,ESDTTransferRole"
          if "SemiFungible" in type_collection: roles_to_add=roles_to_add+",ESDTRoleNFTAddQuantity"
          if "NonFungible" in  type_collection: roles_to_add=roles_to_add+",ESDTRoleNFTUpdateAttributes,ESDTRoleNFTAddURI"
          # t=self.add_account_to_collection(
          #   owner.address,
          #   {"id":collection_id,"type":type_collection},
          #   owner,
          #   roles_to_add=roles_to_add)
          # if "error" in rc and len(rc["error"])>0: return None
          break
    else:
      # log("Erreur de création de la collection. Consulter "+self.getExplorer(owner.public_key.to_address("erd").bech32(),"address"))
      collection_id=None

    return {"id":collection_id,"type":type_collection}


  def create_token(self,name:str,miner:Key,supply=1000000000,decimals=18,properties="canFreeze,canWipe,canPause,canChangeOwner,canUpgrade,canAddSpecialRoles"):
    """
    Création d'un money
    :tags add_token add_money create_money
    :see https://docs.multiversx.com/tokens/esdt-tokens#issuance-of-fungible-esdt-tokens
    :param name:
    :param miner:
    :param supply:
    :param decimals:
    :return:
    """
    name=name[:20]
    assert len(name)>2
    id=name[:10].upper()

    data = "issue" \
          + "@" + str_to_hex(name, False) \
          + "@" + str_to_hex(id, False) \
          + "@" + int_to_hex(supply, False) \
          + "@" + int_to_hex(decimals, False)

    for prop in properties.split(","):
      data=data+ "@" + str_to_hex(prop, False) + "@" + str_to_hex("true",False)

    t=self.create_transaction(miner.address,data=data,
                              value=PRICE_FOR_STANDARD_NFT,
                              receiver=Address.from_bech32(NETWORKS[self.network_type]["esdt"]))
    return t


  def add_account_to_collection(self,account_to_add:str, collection_id:str, owner:str,roles_to_add=DEFAULT_ROLE_FOR_NFT) -> Transaction:
    """
    Ajoute l'ensemble des permissions à un compte
    voir https://docs.multiversx.com/tokens/nft-tokens#assigning-roles
    voir https://docs.multiversx.com/tokens/nft-tokens/#roles
    :param collection_id:
    :param owner:
    :return:
    """

    data = "setSpecialRole" \
           + "@" + str_to_hex(collection_id,False) \
           + "@" + self.toAccount(account_to_add).address.hex()

    for role in roles_to_add.split(","):
      data=data+ "@" + str_to_hex(role,False)

    #if "SemiFungible" in col["type"]: data=data+"@" + str_to_hex("ESDTRoleNFTAddQuantity",False)

    #TODO pour l'instant ne fonctionne pas
    #data=data+ "@" + str_to_hex("ESDTRoleLocalBurn",False);
    #https://devnet-explorer.multiversx.com/transactions/39fa511e01b8801a5d3408d517d279f0c241b723c3eccd4f3a4c41ead3461663#3e9d81eef5b0919311ac056837a2989333924a6562bce00fc6826c43e0eba70f

    contract=Address.from_bech32(NETWORKS[self.network_type]["nft"])
    t=self.create_transaction(miner_addr=owner,data=data,value=0,receiver=contract)
    return t

  def add_collection(self, owner:str, collection_name:str,options:list=[],type_collection="SemiFungible",simulation=False) -> Transaction:
    """
    gestion des collections sur Elrond
    voir https://docs.elrond.com/tokens/nft-tokens/
    :param owner:
    :param collection:
    :param collection_id:
    :param type:
    :return: (identifiant de la collection,vrai s'il y a eu effectivement création)

    TODO: ajouter l'enregistrement de la collection chez Elrond via https://github.com/ElrondNetwork/assets
    """
    collection:str=collection_name.replace(" ","").replace("'","")[:20]
    if collection.lower().startswith("elrond"):
      log("La collection en doit pas commencer par Elrond")
      return None

    collection_id=None
    log("On recherche la collection de nom "+collection_name+" appartenant à "+str(owner))
    for col in self.get_collections(owner, True, type_collection=type_collection):
      if col["name"]==collection_name and owner==col["owner"]:
        log("La collection existe deja, on retourne sont identifiant")
        return col

    if collection_id is None:
      collection_id=collection_name[:8].upper() if collection_id is None else collection_id
      log("La collection n'est pas encore construite, donc on construit "+collection_id)
      #Exemple de requete : issueNonFungible@4d61436f6c6c656374696f6e456c726f6e64@4d41434f4c4c4543@63616e467265657a65@74727565
      #Résultat : https://devnet-explorer.elrond.com/transactions/1e7ac5f911cffce2b846c3f98b8abad636b2958a32df6bebde0ee0b83f087a94
      data = "issue"+type_collection.replace("ESDT","") \
             + "@" + str_to_hex(collection_name, False) \
             + "@" + str_to_hex(collection_id, False)

      log("Ajout des propriétés de la collection. Voir ")
      if type(options)==str: options=options.split(",")
      for key in options:
        data=data + "@" + str_to_hex(key, False)+"@"+str_to_hex("true",False)

      contract=Address.from_bech32(NETWORKS[self.network_type]["nft"])
      t=self.create_transaction(owner,data=data,value=PRICE_FOR_STANDARD_NFT,receiver=contract)

    return t




  def get_nfts_from_collections(self,collections:[str],with_attr=False,format="class",limit=100,offset=0,withOwner=True):
    """
    voirhttps://api.elrond.com/#/collections/CollectionController_getNfts
    :param collections:
    :param miner:
    :return:
    """
    rc=[]
    if type(collections)==str:collections=[collections]
    for col_id in collections:
      #balances=api(self._proxy.url+"/collections/"+col_id+"/accounts?from=0&size="+str(limit))

      result=api(self._proxy.url+"/collections/"+col_id+"/nfts?withOwner="+('true' if withOwner else 'false')+"&withSupply=false&size="+str(limit))
      if result is None: return []
      result=sorted(list(result),key=lambda x:x["nonce"])
      for i in range(offset,offset+len(result)):
        item=result[i]

        if "metadata" in item and "name" in item["metadata"] and "creator" in item["metadata"]:
          item["name"]=item["metadata"]["name"]
          item["attributes"]=item["metadata"]["attributes"]
          item["creator"]=item["metadata"]["creator"]
          item["price"]=item["metadata"]["price"]
          item["symbol"]=item["metadata"]["symbol"]
        royalties=int(item["royalties"]*100) if "royalties" in item else 0
        attributes,description,tags,creators=self.analyse_attributes(item["attributes"] if "attributes" in item else None,with_ipfs=with_attr)

        #On ajoute le propriétaire
        balances=[]
        if withOwner: balances=self.get_balances(nft_addr=item["identifier"]) if "SemiFungible" in item["type"] else {item["owner"]:1}

        nft=NFT(
          name=item["name"],symbol="",
          miner=item["creator"],
          tags=tags,
          collection={"id":col_id},
          attributes=attributes,
          description=description,
          visual=item["media"][0]["url"] if "media" in item else "",
          creators=[item["creator"]],
          royalties=royalties,
          files=item["uris"] if "uris" in item else [],
          supply=int(item["supply"] if "supply" in item else 1),
          price=item["price"] if "price" in item else 0,
          balances=balances
        )

        nft.network=self.network
        nft.address=item["identifier"]
        if format=="class":
          rc.append(nft)
        else:
          rc.append(nft.__dict__)
    return rc



  def get_account(self,addr:str) -> NfluentAccount:
    rc=self.toAccount(addr)
    return NfluentAccount(addr,
                          network=self.network,
                          balance=rc.balance,
                          nfts_balance=self.get_balances(rc.address.bech32()),
                          nonce=rc.nonce,
                          explorer=self.getExplorer(rc.address.bech32(),"address")
                          )


  def get_balances(self, addr:str=None,nft_addr=None,limit=2000,offset=0) -> dict():
    """

    :param addr:
    :param nft_addr: si None on ne retourne pas la balance des nft, si * on retourne toutes les balances
    :return:
    """
    rc=dict()
    if nft_addr is None or len(nft_addr)==0:
      nfts=api(self._proxy.url+"/accounts/"+str(addr)+"/nfts?size=2000")
      if nfts:
        for nft in nfts:
          rc[nft["identifier"]]=(int(nft["balance"]) if "balance" in nft else 1)
    else:
      #https://api.elrond.com/#/collections/CollectionController_getNftAccounts
      accounts=api(self._proxy.url+"/nfts/"+str(nft_addr)+"/accounts?from="+str(offset)+"&size="+str(limit))
      if accounts:
        for acc in accounts:
          rc[acc["address"]]=(int(acc["balance"]) if "balance" in acc else 1)

    return rc




  def get_pem(self,secret_key: bytes, pubkey: bytes):
    name =self._proxy.get_account(pubkey).public_key.to_address("erd").bech32()

    header = f"-----BEGIN PRIVATE KEY for {name}-----"
    footer = f"-----END PRIVATE KEY for {name}-----"

    secret_key_hex = secret_key.hex()
    pubkey_hex = pubkey.hex()
    combined = secret_key_hex + pubkey_hex
    combined_bytes = combined.encode()
    key_base64 = base64.b64encode(combined_bytes).decode()

    payload_lines = textwrap.wrap(key_base64, 64)
    payload = "\n".join(payload_lines)
    content = "\n".join([header, payload, footer])

    return content







  def create_account(self,email="",seed="",domain_appli="",
                     subject="",
                     mail_new_wallet="",mail_existing_wallet="",
                     send_qrcode_with_mail=True,dictionnary={},
                     histo:DAO=None,send_real_email=True) -> Key:
    """
    voir
    :param fund:
    :param name:
    :param seed_phrase:
    :return: Account, PEM,words,qrcode
    """
    if histo:
      pubkey=histo.get_address(email,self.network)
      if pubkey:
        log("Impossible de créer un deuxième compte pour cette adresse "+pubkey)
        if send_real_email:
          url_explorer=self.getExplorer(pubkey,"accounts")
          if len(subject)==0: subject=extract_title_from_html(mail_existing_wallet,dictionnary)
          send_mail(open_html_file(mail_existing_wallet,{
            "wallet_address":pubkey,
            "blockchain_name":"MultiversX",
            "mini_wallet":self.nfluent_wallet_url(pubkey,domain_appli),
            "nfluent_wallet":self.nfluent_wallet_url(pubkey,domain_appli),
            "official_wallet":"https://"+("devnet-" if self.network_type=='devnet' else "")+"wallet.multiversx.com/recover",
            "url_explorer":url_explorer,
            "url_gallery":self.getGallery(pubkey),
          },domain_appli=domain_appli),email,subject=subject)
          return Key(address=pubkey,name=email.split("@")[0],network="elrond")

    log("Création d'un nouveau compte")
    qrcode=""
    if len(seed) == 0:
      mnemonic =Mnemonic.generate()
      words= mnemonic.get_words()

      qr=pyqrcode.create(" ".join(words))
      buffered=io.BytesIO()
      qr.png(buffered,scale=5)

      secret_key = mnemonic.derive_key(0).generate()
      address = str(mnemonic.derive_key(0).generate_public_key().to_address("erd"))

    else:
      secret_key = derive_keys(seed)
      words=seed
      address=self.toAccount(secret_key).address

    log("Création du compte "+self.getExplorer(address,"address"))

    if len(email)>0:
      wallet_appli=self.nfluent_wallet_url(address,domain_appli)
      if not send_qrcode_with_mail:qrcode=None
      if send_real_email:
        url_explorer=self.getExplorer(address,"accounts")

        if send_mail(open_html_file(mail_new_wallet,{
          "wallet_address":address,
          "mini_wallet":wallet_appli,
          "blockchain_name":"MultiversX",
          "url_wallet":self.getWallet(address),
          "url_explorer":url_explorer,
          "encrypted_key":Key(secret_key=secret_key.hex(),address=address).encrypt(),
          "words":" ".join(words),
          "qrcode":"cid:qrcode",
          "access_code":get_access_code_from_email(address)
        },domain_appli=domain_appli),email,subject=subject):
          if histo: histo.add_email(email,address,self.network)

    return Key(secret_key=secret_key.hex(),name=email.split("@")[0],address=address,seed=words,network=self.network_name)


  def analyse_attributes(self,body,with_ipfs=True,timeout=2) -> (list,str,str,list):
    """
    analyse du champs attributes des NFT elrond (qui peut contenir les données onchain ou via IPFS)
    :param body:
    :return: les attributs, description, les tags
    """
    tags=""
    desc=""
    attr=""
    creators=[]
    if body is None: return (attr,desc,tags,creators)

    try:
      attr=str(base64.b64decode(bytes(body,"utf8")),"utf8")
    except:
      attr=str(base64.b64decode(body))

    #log("Pour les attributs, analyse de la chaine "+attr)

    if "tags:" in attr:
      tags=attr.split("tags:")[1].split(";")[0]

    if "metadata" in attr:
      cid=attr.split("metadata:")[1].split(";")[0]
      #log("Recherche des attributs via "+cid)
      cid=cid.split("/props")[0]                                         #Au cas ou le nom du fichier aurait été ajouté dans le cid
      ipfs_url="https://ipfs.io/ipfs/"+cid
      if with_ipfs:
        result=api(ipfs_url,timeout=timeout)
        if not result is None:
          if type(result)==dict:
            attr=result["attributes"] if "attributes" in result else ""
            if "description" in result: desc=result["description"]
            if "creators" in result: creators=result["creators"]
          else:
            desc=result
        else:
          log("Echec de récupération de "+ipfs_url)
          desc="metadata non disponibles"
          attr=""

    else:
      #Analyse d'un fichier json d'attribut dans la description onchain
      if attr.startswith("{\""):attr=" - "+attr
      if " - {\"" in attr:
        sections=attr.split(" - {\"")
        desc=sections[0]
        attr="{\""+attr.split(" - {\"")[1]

        _d=json.loads(attr)
        attr=[]
        for k in _d.keys():
          attr.append({"trait_type":k,"value":_d[k]})

    return (attr,desc,tags,creators)


  def get_nft(self,token_id:str,attr=False,transactions=False,with_balance=None,metadata_timeout=2) -> NFT:
    """
    retourne un NFT complet voir https://api.elrond.com/#/nfts
    :param address:
    :param collection_id:
    :param nonce:
    :return:
    """
    url=self._proxy.url+"/nfts/"+token_id
    item=api(url)

    if item:
      item["attributes"],item["description"],item["tags"],item["creators"]=self.analyse_attributes(item["attributes"],True,timeout=metadata_timeout)
      item["creators"].append({"address":item["creator"],"rate":100,"verified":True})
      nft=NFT(object=item)
      nft.network=self.network
      if with_balance:
        balances=api(url+"/accounts")
        if token_id in balances: nft.balance={with_balance:balances[token_id]}

      item=nft

    return item


  def complete_collection(self,nfts:[NFT]):
    collections=dict()
    for nft in nfts:
        try:
          collection_id=nft.collection["id"]
          if not collection_id in collections: collections[collection_id]=self.get_collection(collection_id)
          nft.collection=collections[collection_id]
        except:
          log("Impossible de compléter "+str(nft))
    return nfts



  def get_owners_of_collections(self, collections:[str]) -> [dict]:
    """
    Récupére les comptes qui peuvent miner des NFTs sur les collections passées en parametre
    voir https://api.elrond.com/#/collections/CollectionController_getNftAccounts
    :param collections:
    :return:
    """
    log("Récupération des propriétaires des collections "+str(collections))
    rc=[]
    for col in collections:
      if len(col)>0:
        result=api(self._proxy.url.replace("gateway","api")+"/collections/"+col)
        if "roles" in result:
          for r in result["roles"]:
            if r["canCreate"]:      #On récupére les comptes qui ont le droit de créer des NFT
              rc.append(self.get_account(r["address"]))

    return rc


  def extract_visual_from_nft(self,nft):
    if not "media" in nft or len(nft["media"])==0:
      url=nft["url"]
    else:
      url=nft["media"][0]["originalUrl"]
      if "ipfs" in url:
        url=nft["url"]

    return url


  def get_nfts(self,_user:AccountOnNetwork,limit=2000,with_attr=False,offset=0,with_collection=False,type_token="NonFungibleESDT,SemiFungibleESDT") -> [NFT]:
    """
    https://docs.multiversx.com/tokens/nft-tokens
    voir
    :param _user:
    :param limit:
    :param with_attr:
    :return:
    """
    _user:AccountOnNetwork=self.toAccount(_user)
    if _user is None:return []
    owner=_user.address.bech32()
    rc:[NFT]=[]
    balances=self.get_balances(owner)

    #nfts:dict=api(self._proxy.url+"/address/"+_user.public_key.to_address("erd").bech32()+"/esdt")
    nfts=[]
    for type_t in type_token.split(","):
      if not type_t.endswith("ESDT"):type_t=type_t+"ESDT"
      #voir https://api.multiversx.com/#/accounts/AccountController_getAccountNfts
      result:list=api(self._proxy.url+"/accounts/"+owner+"/nfts?withSupply=true&type="+type_t+"&size="+str(limit))
      result = sorted(result, key=lambda d: d['nonce'],reverse=True)
      if result is None:
        log("Le compte "+owner+" n'existe pas")
        return []
      nfts=nfts+result

    #nfts=list(nfts["data"]["esdts"].values())
    if len(nfts)<offset:return []

    collections=dict()
    for nft in nfts[offset:limit]:
      _data={}
      metadata=nft["metadata"] if "metadata" in nft else {}
      if metadata==dict():
        if "attributes" in nft:
          nft["attributes"],nft["description"],nft["tags"],nft["creators"]=self.analyse_attributes(nft["attributes"],with_attr)
      else:
        for k in [("attributes",[]),("creators",[]),("descriptions",""),("tags",""),("name",""),("price",0),("symbol","")]:
          nft[k[0]]=extract_from_dict(metadata,k[0],k[1])

      collection_id,nonce=self.extract_from_tokenid(nft["identifier"])
      if not collection_id in collections.keys():
        collections[collection_id]=self.get_collection(collection_id) if with_collection else {"id":collection_id}

      collection=collections[collection_id]
      if not "royalties" in nft or nft["royalties"]=="": nft["royalties"]=0
      nft["owner"]=_user.address.bech32()

      _nft=NFT(
        object=nft,
        collection=collection,
        visual=self.extract_visual_from_nft(nft),
        creators=[{"address":nft["creator"],"share":int(nft["royalties"])/100}] if not "creators" in _data else _data["creators"],
      )
      _nft.balances={_user.address.bech32():balances[_nft.address] if _nft.address in balances else 0}
      _nft.network="elrond-"+self.network

      if _nft.address:      #Pas d'insertion des NFT n'ayant pas d'adresse
        rc.insert(0,_nft)

      if len(rc)>limit:break

    return rc



  def freeze(self,_user,token_id):
    """
    https://docs.elrond.com/developers/nft-tokens/
    :param _user:
    :param token_id:
    :return:
    """
    _user=self.find_key(_user)
    collection_id,nonce=self.extract_from_tokenid(token_id)
    data = "freezeSingleNFT@" + str_to_hex(collection_id) \
           + "@" + int_to_hex(nonce,4) \
           + "@" + str_to_hex(_user.address, False)
    t = self.send_transaction(_user,
                              self._proxy.get_account(address=NETWORKS[self.network_type]["nft"]),
                              _user,
                              data=data)
    return t


  def burn(self,token_id,_user:Key,quantity=1,backup_address="") -> Transaction:
    """
    https://docs.multiversx.com/tokens/nft-tokens#burn-quantity
    :param _user:
    :param token_id:
    :return:
    """
    collection,nonce=self.extract_from_tokenid(token_id)
    data = "ESDTNFTBurn@" + str_to_hex(collection,False) + "@" + nonce + "@" + int_to_hex(quantity,4)
    t=self.create_transaction(_user,data)
    # t = self.send_transaction(_user,_user.address , _user,  data=data)
    # if t["error"]!="" and len(backup_address)>0:
    #   t=self.transfer(token_id,_user,backup_address,quantity)
    return t



  def update(self,user,token_id,properties,ipfs):
    _user=self.toAccount(user)
    collection_id,nonce=self.extract_from_tokenid(token_id)
    cid_metadata=ipfs.add(properties)
    tags=""
    s="metadata:"+cid_metadata["Hash"]+"/props.json;tags:"+("" if len(tags)==0 else " ".join(tags))
    data = "ESDTNFTUpdateAttributes" \
           + "@" + str_to_hex(collection_id,False) \
           + "@" + int_to_hex(int(nonce),4) \
           + "@" + str_to_hex(s, False)
    t = self.send_transaction(_user, _user, _user, data=data)
    if t["status"]=="invalid":
      return {"error":"requete invalide "+t["hyperblockHash"]}
    else:
      return {"result":{"transaction":t["hyperblockHash"]}}



  def canMintOnCollection(self,miner_addr:str,collection:dict,quantity=1):
    if collection is None: return False
    if not "type" in collection or not "roles" in collection:
      collection=self.get_collection(collection["id"])
    if (quantity>1 and collection["type"]!="SemiFungibleESDT"): return False
    for role in collection["roles"]:
      if role["address"]==miner_addr and role["canCreate"]:
          return True
    return False


  def get_tokens(self,filter,_type="FungibleESDT",with_detail=False,limit=100) -> list:
    """
    voir #https://api.multiversx.com/#/tokens/TokenController_getTokens
    :param filter:
    :param type:
    :param with_detail:
    :return:
    """
    if not _type.endswith("ESDT"):_type=_type+"ESDT"
    rc=[]
    size=1000
    offset=0
    sort="&sort=transactions&order=desc"
    while True:
      if filter.startswith("erd") and len(filter)>15:
        url=self._proxy.url+"/accounts/"+filter+"/tokens?includeMetaESDT=true&size="+str(size)+"&from="+str(offset)+sort
      else:
        url=self._proxy.url+"/tokens?from="+str(offset)+"&size="+str(size)+("&search="+filter if filter!='' else "")+"&type="+_type+sort
      if with_detail: url=url+"&includeMetaESDT=true"

      result=requests.get(url)

      if len(filter)>0 and len(result.json())==0:
        url=self._proxy.url+"/tokens?from="+str(offset)+"&size="+str(size)+"&name="+filter+"*&type="+_type+("&includeMetaESDT=true" if with_detail else "")+sort
        result=requests.get(url)

      if result.status_code==200:
        rc=rc+result.json()
        if len(result.json())<size: break
        offset=offset+size
      else:
        break

    for i,t in enumerate(rc):
      rc[i]["id"]=rc[i]["identifier"]
      rc[i]["image"]=rc[i]["assets"]["pngUrl"] if "assets" in rc[i] else "https://tokenforge.nfluent.io/assets/icons/egld-token-logo.webp"
      rc[i]["descripion"]=rc[i]["assets"]["description"] if "assets" in rc[i] else ""
      rc[i]["balance"]=round(int(rc[i]["balance"])/1e20)*100 if "balance" in rc[i] else ""
      rc[i]["url"]=rc[i]["assets"]["website"] if "assets" in rc[i] and "website" in rc[i]["assets"] else ""

    if filter=="" or filter.startswith("erd"):
      token={
        "id":"egld","identifier":"egld",
        "image":"https://tokenforge.nfluent.io/assets/icons/egld-token-logo.webp",
        "name":"eGld" if self.network_type=='mainnet' else "xEgld",
        "description":"Le token natif de la blockchain multiversX",
        "balance":0
        }
      if filter.startswith("erd"):
        token["balance"]=self.balance(filter)/1e18
        token["url"]=self.getWallet()

      if not filter.startswith("erd") or token["balance"]>0: rc.insert(0,token)
    return rc




  def get_token(self,token_id:str) -> dict:
    if token_id.lower()=="egld":
      rc={"name":"egld","identifier":"egld","supply":21000000,"unity":"eGLD","decimals":18}
    else:
      rc=self._proxy.get_definition_of_fungible_token(token_id).__dict__
    return {"name":rc["name"],"id":rc["identifier"],"supply":rc["supply"],"unity":rc["name"],"decimals":rc["decimals"]}


  def get_min_gas_for_transaction(self,n_transactions=1) -> float:
    return 0.001*n_transactions


  def analyse_mint_transaction(self,t) -> dict :
    if t["status"]!="success":
      return {
        "error":"invalid",
        "tx":t["hash"],
        "explorer":self.getExplorer(t["hash"])
      }

    events = t["logs"]["events"]

    #TODO: a corriger
    nftaddress=t["result"]["mint"] if "result" in t else ""
    id,nonce = self.extract_from_tokenid(nftaddress)
    miner_addr=""

    for e in events:
      if e["identifier"]=='ESDTNFTCreate':
        nonce= e["topics"][1]
    rc={
      "error":"",
      "tx":str(t["hash"]),
      "result":{"transaction":str(t["hash"]),"mint":id+"-"+nonce},
      "balance":0,
      "link_mint":self.getExplorer(id+"-"+nonce,"nfts"),
      "link_transaction":self.getExplorer(t["hash"]),
      "link_gallery":self.getGallery(miner_addr),
      "link_nft_gallery":self.getGallery(id+"-"+nonce,"nfts/"),
      "out":"",
      "cost":0,
      "unity":"egld",
      "command":"insert"
    }
    return rc






  def getRoleForToken(self,collection):
    payload={
      "scAddress":NETWORKS[self.network_type]["nft"],
      "funcName":"getSpecialRoles",
      "args":[str_to_hex(collection,False)]
    }
    result=self._proxy.query_contract(payload)
    if result.data["returnCode"]=="ok":
      rc=[]
      for data in result.data["returnData"]:
        dt=str(base64.b64decode(data),"utf8")
        rc.append({"account":dt.split(":")[0],"roles":dt.split(":")[1].split(",")})
    else:
      log("Probléme de lecture des droits")
      return []

    return rc

  def get_costs(self):
    costs=[]
    prices=requests.get("https://api.multiversx.com/mex/tokens").json()
    for price in prices:
      if price["symbol"]=="WEGLD":
        costs=requests.get(self._proxy.url+"/network/gas-configs").json()["data"]["gasConfigs"]["builtInCost"]
        for k in costs.keys():
          costs[k]={"egld":costs[k],"usd":price["price"]*costs[k]/1e18}

    return costs





  def toAccount(self, user) -> AccountOnNetwork:
    """
    retourne l'objet account pour le réseau
    :param user:
    :return:
    """
    if type(user)==dict:
      if "address" in user:
        user=user["address"]
      else:
        if "address" in user:user=user["address"]

    if type(user)==bytes:
      address=UserSecretKey(user).generate_public_key().to_address("erd").bech32()
      user=Key(secret_key=user.hex(),address=address,network="elrond")

    if type(user)==str and len(user)>0:
      if user.startswith("erd"):
        user=self.find_key(user)
      else:
        if len(user.split(" "))>10:                     #on identifie une suite de mots
          secret_key = derive_keys(user.strip())
          address=UserSecretKey(secret_key).generate_public_key().to_address("erd").bech32()
          user=self._proxy.get_account(address=Address.from_bech32(address))
          user.secret_key=secret_key.hex()
          return user
        else:
          address=UserSecretKey(bytes.fromhex(user)).generate_public_key().to_address("erd").bech32()
          user=Key(secret_key=user,address=address,network="elrond")

    if type(user)==Key:
      if user.address=="":
        user.address=UserSecretKey(bytes.fromhex(user.secret_key)).generate_public_key().to_address("erd").bech32()

      _user=self._proxy.get_account(address=Address.from_bech32(user.address))
      _user.secret_key=user.secret_key
      return _user




    #
    # if user.startswith("erd"):
    #   user=self._proxy.get_account(address=user)
    # else:
    #   key=self.find_key(user)
    #   user=self._proxy.get_account(address=Address.from_bech32(key.address))
    #   user.secret_key=key.secret_key

      # pem_file=ELROND_KEY_DIR+user+(".pem" if not user.endswith('.pem') else '')
      # if exists(pem_file):
      #
      #   with open(pem_file,"r") as file:
      #     txt=file.read()
      #     if txt.startswith("-----BEGIN PRIVATE KEY"):
      #       user=UserPEM.from_file(path=Path(pem_file))
      #     else:
      #       words=""
      #       for s in txt.split("\n "):
      #         if len(s)>1:
      #           if " " in s:
      #             words=words+s.split(" ")[1]+" "
      #           else:
      #             words=words+s
      #       words=words.replace("\n","").strip()
      #       secret_key, pubkey = derive_keys(words)
      #       user=self.proxy.get_account(address=Address(pubkey).bech32())
      #       user.secret_key=secret_key.hex()
      # else:
      #   return None

    return user



  def extract_from_tokenid(self, token_id) -> (str,str):
    nonce=""
    collection_id=""

    l_fields=len(token_id.split("-"))
    if l_fields>1:
      collection_id=token_id.split("-")[0]+"-"+token_id.split("-")[1]
    if l_fields>2:
      nonce=token_id.split("-")[2]

    return collection_id,nonce


  def balance(self,account:AccountOnNetwork):
    if type(account)!=AccountOnNetwork: account=self.toAccount(account)
    return self._proxy.get_account(account.address).balance



  def get_keys(self,qrcode_scale=0,address="") -> [Key]:
    """
    retourne l'ensemble des clé ou une seul filtré par l'adresse ou le nom
    :param qrcode_scale:
    :param with_balance:
    :param address:
    :return:
    """
    rc=[]
    #log("Lecture des clés "+str(listdir(ELROND_KEY_DIR)))
    for f in listdir(ELROND_KEY_DIR)+self.keys:
      if f.endswith(".pem"): #or f.endswith(".json"):
        acc=UserPEM.from_file(path=Path(ELROND_KEY_DIR+f))
        secret_key=acc.secret_key.hex()
        name=f.replace(".pem","").replace(".json","")

        if len(address)==0 or (name==address or acc.public_key.to_address("erd").bech32()==address):
          k=Key(name=name,
                address=acc.public_key.to_address("erd").bech32(),
                secret_key=secret_key,
                explorer=self.getExplorer(address,"accounts"),
                network="elrond")
          rc.append(k)

    return rc


  def convert_keystore_to_key(self, keystore, password,address_index: Optional[int] = None):
    keystore_content=str(base64.b64decode(keystore.split("base64,")[1]),"utf8")
    key_file_object = json.loads(keystore_content)
    kind = key_file_object.get("kind", UserWalletKind.SECRET_KEY.value)
    if kind == UserWalletKind.SECRET_KEY.value:
      if address_index is not None: raise Exception("address_index must not be provided when kind == 'secretKey'")
      secret_key = UserWallet.decrypt_secret_key(key_file_object, password)
    elif kind == UserWalletKind.MNEMONIC.value:
      mnemonic = UserWallet.decrypt_mnemonic(key_file_object, password)
      secret_key = mnemonic.derive_key(address_index or 0)

    address=secret_key.generate_public_key().to_address("erd").bech32()
    return Key(name="",address=address,network=self.network,secret_key=secret_key.hex())



  def find_key(self,address_or_name) -> Key:
    """
    Trouve la clé sur le serveur
    :param address_or_name:
    :return:
    """
    if type(address_or_name)==Key: return address_or_name
    if type(address_or_name)==AccountOnNetwork:
      address_or_name=address_or_name.address.bech32()

    if len(address_or_name)>50 and not address_or_name.startswith("erd"):
      return Key(encrypted=address_or_name)

    for k in self.get_keys():
      if k.address==address_or_name or k.name==address_or_name:
        return k

    return Key(address=address_or_name)


  def create_transaction(self,miner_addr:str,data:str,value=0,receiver=None) -> Transaction:
    """

    :param _miner:
    :param data:
    :return:
    """

    _miner=self.toAccount(miner_addr)
    if receiver is None:receiver=_miner.address

    config:NetworkConfig=self._proxy.get_network_config()
    t=Transaction(
      nonce=_miner.nonce,
      sender=_miner.address,
      receiver=receiver,
      gas_limit=LIMIT_GAS,
      value=int(value*1e18),
      gas_price=config.min_gas_price,
      chain_id=config.chain_id,
      version=1
    )

    if not data is None:
      t.data = TransactionPayload.from_str(data)
    else:
      t.data=TransactionPayload(bytes())

    return t



  def get_owners_of_nft(self, nft_addr:str) -> [NfluentAccount]:
    """
    voir https://devnet-api.multiversx.com
    :param address:
    :return:
    """
    result=api(self._proxy.url+"/nfts/"+nft_addr+"/accounts")
    rc=[NfluentAccount(address=x["address"]) for x in result]
    return rc



  def jsonify_transaction(self,t:Transaction) -> dict:
    rc= t.to_dictionary(True)
    return rc



  def mint(self, nft:NFT, storage:Storage,price=0) -> Transaction:
    """
	 Fabriquer un NFT au standard elrond
	 https://docs.elrond.com/tokens/nft-tokens/#nftsft-fields

	 l'ajout du domain_server est nécessaire pour respecter l'interface

	 :type storage: object
	 :param contract:
	 :param user_from:
	 :param arguments:
	 :return:
	 """

    if len(nft.attributes)>0 or len(nft.tags)>0 or len(nft.creators)>0 or price>0 or len(nft.symbol)>0:
      _metadata={
        "name":nft.name,
        "id":now("hex"),
        "description":nft.description,
        "attributes":nft.attributes,
        "creators":nft.creators,
        "price":str(price),
        "symbol":nft.symbol
      }

      try:
        cid=storage.add(_metadata)
      except:
        return returnError("!Impossible de mettre les metadata en ligne sur le noeud IPFS propriétaire")

      log("Address des metadata: "+cid["url"])
      url_metadata=cid["url"]
      s="metadata:"+cid["cid"]
      if len(nft.tags)>0: s=s+",tags:"+nft.tags
      _h=get_hash(_metadata)
      if len(_h) % 2!=0: _h="0"+_h
    else:
      url_metadata=""
      s=nft.description
      _h="00"

    #Traitement de la problématique des caractères spéciaux
    s=strip_accents(s.replace("\n"," "))
    title=strip_accents(nft.name)
    log("tags et attributes : "+s)

    #hash = hex(int(now() * 1000)).upper().replace("0X", "")


    #Exemple de creation:
    #ESDTNFTCreate@4d41434f4c4c4543542d323565666366@01@4d6f6e546f6b656e@09c4@516d63636265345a78434b72706471587772784841377979347473635563465a4a6931724c69414d624d6a643252@746167733a3b6d657461646174613a516d5947397a6e724c7a735252594d436d6e52444a7931436f7478676e4a384b6a5668746870485a553775436d59@68747470733a2f2f697066732e696f2f697066732f516d63636265345a78434b72706471587772784841377979347473635563465a4a6931724c69414d624d6a643252

    #voir https://docs.multiversx.com/tokens/nft-tokens/#creation-of-an-nft
    log("Tentative de création de NFT par "+self.getExplorer(nft.owner)+" sur la collection "+self.getExplorer(nft.collection["id"],"collections"))
    method="ESDTNFTCreate"
    data = method \
           + "@" + str_to_hex(nft.collection["id"],False) \
           + "@" + int_to_hex(nft.supply,6) \
           + "@" + str_to_hex(title, False) \
           + "@" + int_to_hex(nft.royalties*100,4) \
           + "@" + _h \
           + "@" + str_to_hex(s,False) \
           + "@" + str_to_hex(nft.visual,False)

    if len(url_metadata)>0: data=data+ "@" + str_to_hex(url_metadata,False)

    for f in nft.files:
      if not f is None and len(f)>0:
        data=data+"@"+str_to_hex(f,False)

    #Exemple de minage: ESDTNFTCreate@544f5552454946462d323864383938@0a@4c6120746f75722071756920636c69676e6f7465@09c4@516d64756e4a7a71377850443164355945415a6952647a34486d4d32366179414d574334687a63785a447735426b@746167733a3b6d657461646174613a516d54713845666d36416634616a35383847694d716b4d44524c475658794133773439315052464e413471546165@68747470733a2f2f697066732e696f2f697066732f516d64756e4a7a71377850443164355945415a6952647a34486d4d32366179414d574334687a63785a447735426b

    #Exemple : Pass5An a 10 exemplaire avec le fichier png chargé et description dans description et tag dans tags
    # resultat ESDTNFTCreate@43414c5649323032322d356364623263@0a@5061737331416e@09c4@516d50373347703135464461367976474474397765526d7035684d575041734c4c63724e5a686d506e79366d4134@746167733a3b6d657461646174613a516d54713845666d36416634616a35383847694d716b4d44524c475658794133773439315052464e413471546165@68747470733a2f2f697066732e696f2f697066732f516d50373347703135464461367976474474397765526d7035684d575041734c4c63724e5a686d506e79366d4134
    # exemple : ESDTNFTCreate@544f555245494646454c2d333535613733@0a@5669736974654c6534417672696c32303232@09c4@516d5531394736544c4b704b38436a504c5137726e4d4c4868553346784257317846696b44335a48665a476a6841@746167733a3b6d657461646174613a516d54713845666d36416634616a35383847694d716b4d44524c475658794133773439315052464e413471546165@68747470733a2f2f697066732e696f2f697066732f516d5531394736544c4b704b38436a504c5137726e4d4c4868553346784257317846696b44335a48665a476a6841
    # traduction : ESDTNFTCreate@TOUREIFFEL-355a73@@VisiteLe4Avril2022@2500@QmU19G6TLKpK8CjPLQ7rnMLHhU3FxBW1xFikD3ZHfZGjhA@tags:;metadata:QmTq8Efm6Af4aj588GiMqkMDRLGVXyA3w491PRFNA4qTae@https://ipfs.io/ipfs/QmU19G6TLKpK8CjPLQ7rnMLHhU3FxBW1xFikD3ZHfZGjhA
    # transaction : 0652f69168b908faeb497b9fdee8593e747ee759349083f55b2e4ad17de1e2c3

    # data = data +  "@" + str_to_hex(hash, False) + "@"
    # for k in properties.keys():
    #     if k != "title":
    #         data = data + str_to_hex(k + ":" + properties[k] + ",", False)
    # data = data + "@" + str_to_hex(visual, False)

    #if type(value)==int or type(value)==float: value=TokenPayment.egld_from_amount(str(value))

    transaction = self.create_transaction(miner_addr=nft.miner,data=data)
    return transaction




