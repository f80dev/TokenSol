import base64
import io

from flaskr.Keys import Key
from flaskr.NFluentAccount import NfluentAccount
from flaskr.dao import DAO
import json
import sys
import time
from os import listdir
from os.path import exists
from time import sleep
import pyqrcode
from flaskr.Tools import  hex_to_str, now, get_access_code_from_email, int_to_hex, str_to_hex, log, api, \
  send_mail, open_html_file, strip_accents, returnError, decrypt
from flaskr.NFT import NFT
import textwrap


from erdpy import config
from erdpy.wallet.core import generate_mnemonic
from erdpy.proxy import ElrondProxy
from erdpy.transactions import Transaction
from erdpy.accounts import Account,Address
from erdpy.wallet import derive_keys
from flaskr.Network import Network

RESULT_SECTION="smartContractResults"
LIMIT_GAS=200000000
PRICE_FOR_STANDARD_NFT=50000000000000000

ELROND_KEY_DIR="./Elrond/PEM/"      #Le repertoire de travail etant server

#voir https://docs.multiversx.com/tokens/nft-tokens/
# DEFAULT_OPTION_FOR_ELROND_COLLECTION={
#   "canFreeze":"True",
#   "canWipe":"True",
#   "canPause":"True",
#   "canTransferNFTCreateRole":"True",
#   "canChangeOwner":"True",
#   "canUpgrade":"True",
#   "canAddSpecialRoles":"True"
# }

DEFAULT_ROLE_FOR_ELROND_COLLECTION={
  "ESDTRoleNFTCreate":"True",
  "ESDTRoleNFTBurn":"True",
  "ESDTRoleNFTUpdateAttributes":"True",
  "ESDTRoleNFTAddURI":"True",
  "ESDTTransferRole":"True",
  "ESDTRoleNFTAddQuantity":"True"
}


NETWORKS={
  "testnet":{
    "unity":"xEgld",
    "faucet":"https://r3d4.fr/elrond/testnet/index.php",
    "proxy":"https://testnet-api.multiversx.com",
    "explorer":"https://testnet-explorer.multiversx.com",
    "wallet":"http://testnet-wallet.multiversx.com",
    "nft":"erd1qqqqqqqqqqqqqqqpqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqzllls8a5w6u",
    "shard":0
  },

  #erd1qqqqqqqqqqqqqpgqkwfvpkaf6vnn89508l0gdcx26vpu8eq5d8ssz3lhlf
  "devnet":{
    "unity":"xEgld",
    "identifier":"TFE-116a67",
    "faucet":"https://r3d4.fr/elrond/devnet/index.php",
    "proxy":"https://devnet-api.multiversx.com",
    "explorer":"https://devnet-explorer.multiversx.com",
    "wallet":"https://devnet-wallet.multiversx.com",
    "nft":"erd1qqqqqqqqqqqqqqqpqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqzllls8a5w6u",
    "shard": 1
  },

  "mainnet":{
    "unity":"Egld",
    "identifier":"",
    "faucet":"",
    "proxy":"https://api.multiversx.com",
    "explorer":"https://explorer.multiversx.com",
    "wallet":"https://wallet.multiversx.com",
    "nft":"erd1qqqqqqqqqqqqqqqpqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqzllls8a5w6u",
    "shard": 1
  }
}


class Elrond(Network):

  def __init__(self,network="elrond-devnet"):
    super().__init__(network)
    self._proxy=ElrondProxy(NETWORKS[self.network_type]["proxy"])
    self.transactions=[]


  def get_unity(self):
    return "eGLD"

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




  def get_transactions(self,address,limit=1000,size=10,profondeur=0,profondeur_max=3,methods=[],exclude_addresses=[]):
    """
    voir
    :return:
    """
    result=api(self._proxy.url.replace("gateway","api")+"/accounts/"+address+"/transactions?status=success&from=0&size="+str(size)) if len(self.transactions)<limit else None
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

          if method=="ESDTNFTTransfer":
            try:
              data[4]=data[4].replace("\'","")
              addr=data[4] if len(data[4]) % 2==0 else "0"+data[4]
              receiver=Account(address=addr).address.bech32()
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




  def getExplorer(self, tx="", type="transactions") -> str:
    url = NETWORKS[self.network_type]["explorer"] + "/" + type + "/"
    if len(tx)>0:url=url+tx
    url=url.replace("api","explorer")
    return url

  def getWallet(self,addr=""):
    return NETWORKS[self.network_type]["wallet"] + "/" + addr



  def send_transaction(self, _sender: Key,
                       _receiver: Account,
                       _sign: Key,
                       value: str, data: str,
                       gas_limit=LIMIT_GAS, timeout=120):
    """
    Envoi d'une transaction signée
    :param _sender:
    :param _receiver:
    :param _sign:
    :param value:
    :param data:
    :return:
    """
    _sender=self.toAccount(_sender)
    _sign=self.toAccount(_sign)

    _sender.sync_nonce(self._proxy)
    t = Transaction()
    t.nonce = _sender.nonce
    t.version = config.get_tx_version()
    t.data = data
    t.chainID = self._proxy.get_chain_id()
    t.gasLimit = gas_limit
    t.value = str(value)
    t.sender = _sender.address.bech32()
    t.receiver = _receiver.address.bech32()
    t.gasPrice = config.DEFAULT_GAS_PRICE

    log("On signe la transaction avec le compte " + self.getExplorer(_sign.address.bech32(),"address"))
    t.sign(_sign)

    try:
      tx = t.send_wait_result(self._proxy,timeout=timeout)
      log("Execution de la transaction " + data + " : " + self.getExplorer(tx.raw["sender"],"address"))

      d=tx.raw
      d["explorer"]=self.getExplorer(d["hash"])
      d["error"]=""
      return d
    except Exception as inst:

      mess=str(inst.args).split(":")
      mess=":".join(mess[2:]) if len(mess)>2 else ":".join(mess)
      mess=mess.strip()
      log("Exception d'execution de la requete " + mess)
      if mess.startswith("{"):
        mess=(mess.split("}")[0]+"}").replace("'","\"").replace("None","\"\"")
        return json.loads(mess)

      return mess




  def get_collections(self, addr:str, detail:bool=True, type_collection="", special_role=""):
    """
    récupération des collections voir : https://devnet-api.multiversx.com/#/accounts/AccountController_getAccountCollectionsWithRoles
    :param creator:
    :param fields:
    :return:
    """
    if type(addr)==Account: addr=addr.address.bech32()
    if addr.startswith("erd"):
      owner=self.toAccount(addr).address.bech32()
      url=self._proxy.url+"/accounts/"+owner+"/roles/collections/?size=500"
      if len(type_collection)>0:
        if not "ESDT" in type_collection:type_collection= type_collection + "ESDT"
        url= url +"&type=" + type_collection

      if len(special_role)==0:
        url=url+"&owner="+owner
      else:
        url=url+"&"+special_role+"=true"


      result=api(url,"gateway=api")
      if not result is None:
        cols=result
      else:
        log("Bug: Impossible de récupérer les NFTs de "+addr)
        return []
    else:
      cols=[self.get_collection(addr)]
    rc=[]
    for _col in cols:
      if not "id" in _col: _col["id"]=_col["collection"]
      if "role" in _col:
        if "roles" in _col["role"]:
          del _col["role"]["roles"]

        if not "roles" in _col:
          _col["roles"]=[_col["role"]]
          del _col["role"]

      if not "address" in _col["roles"][0]: _col["roles"][0]["address"]=_col["owner"]

      _col["link"]="https://"+("devnet." if "devnet" in self.network else "")+"inspire.art/collections/"+_col["id"]
      if len(type_collection)==0 or type_collection in _col["type"]:
        rc.append(_col)

    rc=sorted(rc,key=lambda x:x["timestamp"] if "timestamp" in x else 0,reverse=True)

    if detail:
      for item in rc:
        item["id"]=item["ticker"]
        item["options"]={
          "canFreeze":item["canFreeze"],
          "canTransfer":item["canTransfer"],
          "canWipe":item["canWipe"],
          "canPause":item["canPause"],
          "canTranferNftCreateRole":item["canTransferNftCreateRole"]
        }

    return rc



  def get_collection(self,collection_id):
    rc=api(self._proxy.url+"/collections/"+collection_id,"gateway=api")
    if not rc is None:
      if "ticker" in rc:
        rc["id"]=rc["ticker"]
      else:
        rc["id"]=rc["collection"]

    if not "roles" in rc:
      if "role" in rc:
        rc["roles"]=[rc["role"]]
      else:
        rc["roles"]=[{"address":rc["owner"]}]
        for k in ["canCreate",  "canBurn",  "canAddQuantity",  "canAddUri", "canUpdateAttributes"]:
          rc["roles"][0][k]=rc[k] if k in rc else False

      rc["roles"][0]["address"]=rc["owner"]

    if "roles" in rc:
      for r in rc["roles"]:
        del r["roles"]

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



  def transfer(self,nft_addr:str,miner:Key,to_addr:str,quantity=1):
    """
    Transfert d'un NFT
    voir https://docs.multiversx.com/tokens/nft-tokens/#transfers
    :param collection_id:
    :param nonce:
    :param _from:
    :param _to:
    :return:
    """
    _from=self.toAccount(miner)

    if not self.find_key(_from):
      returnError("!Impossible de transférer sans la clé secret du propriétaire")

    _to=self.toAccount(to_addr)
    if _to is None:
      log("Destinataire inconnu")
      return False

    if _from.address.bech32()==_to.address.bech32(): return False

    log("Transfert de "+nft_addr+" de "+_from.address.bech32()+" a "+_to.address.bech32())
    collection_id,nonce=self.extract_from_tokenid(nft_addr)
    data = "ESDTNFTTransfer" \
           + "@" + str_to_hex(collection_id,False) \
           + "@" + nonce \
           + "@" + int_to_hex(quantity) \
           + "@" + _to.address.hex()
    t = self.send_transaction(_from, _from, _from, 0, data)
    if t is None or t["status"]!="success":
      return {"error":"Echec du transfert","hash":t["hash"],"explorer":self.getExplorer(t["hash"])}
    else:
      t["error"]=""
      return t


  def add_account_to_collection(self,account_to_add:str, col:dict, owner:Key,
                                roles_to_add="ESDTRoleNFTCreate,ESDTRoleNFTBurn") -> dict:
    """
    Ajoute l'ensemble des permissions à un compte
    voir https://docs.multiversx.com/tokens/nft-tokens#assigning-roles
    :param collection_id:
    :param owner:
    :return:
    """
    owner=self.toAccount(owner)
    account_to_add=self.toAccount(account_to_add)

    data = "setSpecialRole" \
           + "@" + str_to_hex(col["id"],False) \
           + "@" + account_to_add.address.hex()

    for role in roles_to_add.split(","):
      data=data+ "@" + str_to_hex(role,False)

    if "SemiFungible" in col["type"]:
      data=data+"@" + str_to_hex("ESDTRoleNFTAddQuantity",False)

    #TODO pour l'instant ne fonctionne pas
    #data=data+ "@" + str_to_hex("ESDTRoleLocalBurn",False);
    #https://devnet-explorer.multiversx.com/transactions/39fa511e01b8801a5d3408d517d279f0c241b723c3eccd4f3a4c41ead3461663#3e9d81eef5b0919311ac056837a2989333924a6562bce00fc6826c43e0eba70f

    t = self.send_transaction(_sender=owner,
                              _receiver=Account(address=NETWORKS[self.network_type]["nft"]),
                              _sign=owner, value=0, data=data)

    sleep(2.0)

    return t



  def add_collection(self, owner:Key, collection_name:str,options:list=[],type_collection="SemiFungible") -> (dict):
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
    log("On recherche la collection de nom "+collection_name+" appartenant à "+owner.address)
    for col in self.get_collections(owner.address, True, type_collection=type_collection):
      if col["name"]==collection_name and owner.address==col["owner"]:
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
      for key in options:
        data=data + "@" + str_to_hex(key, False)+"@"+str_to_hex("true",False)

      t = self.send_transaction(owner,
                                Account(address=NETWORKS[self.network_type]["nft"]),
                                owner,
                                str(PRICE_FOR_STANDARD_NFT),
                                data)

      if "error" in t and len(t["error"])>0:
        log("BUG: "+t["error"]+" consulter "+self.getExplorer(owner.address.bech32(),"address"))
        return None

      sleep(1)

      if RESULT_SECTION in t:
        log("Recherche du collection id")
        for result in t[RESULT_SECTION]:
          if len(result["data"].split("@"))>2:
            collection_id = hex_to_str(result["data"].split("@")[2])
            rc=self.add_account_to_collection(owner.address,{"id":collection_id,"type":type_collection}, owner)
            if "error" in rc: return None
            break
      else:
        log("Erreur de création de la collection. Consulter "+self.getExplorer(owner.address.bech32(),"address"))
        collection_id=None

    return {"id":collection_id,"type":type_collection}


  def get_nfts_from_collections(self,collections:[str],with_attr=False,format="class"):
    """
    voir https://api.elrond.com/#/collections/CollectionController_getNftCollection
    :param collections:
    :param miner:
    :return:
    """
    rc=[]
    for col_id in collections:
      result=api(self._proxy.url+"/collections/"+col_id+"/nfts?withOwner=true&withSupply=true","gateway=api")
      result=sorted(list(result),key=lambda x:x["nonce"])
      for i in range(len(result)):
        item=result[i]
        royalties=int(item["royalties"]*100) if "royalties" in item else 0
        attributes,description,tags=self.analyse_attributes(item["attributes"],with_ipfs=with_attr)
        nft=NFT(
          name=item["name"],symbol="",
          miner=item["creator"],
          owner=item["owner"],
          tags=tags,
          collection={"id":col_id},
          attributes=attributes,
          description=description,
          visual=item["media"][0]["url"],
          creators=[item["creator"]],
          royalties=royalties,
          files=item["uris"],
          supply=int(item["supply"]),
          price=0
        )
        nft.network=self.network
        nft.address=item["identifier"]
        if format=="class":
          rc.append(nft)
        else:
          rc.append(nft.__dict__)
    return rc



  def get_account(self,addr:str) -> NfluentAccount:
    rc=self._proxy.get_account(self.toAccount(addr).address)
    return NfluentAccount(addr,network=self.network,balance=int(rc["balance"]),nonce=rc["nonce"],explorer=self.getExplorer(addr,"address"))


  def get_balances(self, addr:str,nft_addr=None):
    rc={"egld":int(self._proxy.get_account(Address(addr))["balance"])}
    nfts=api(self._proxy.url+"/accounts/"+str(addr)+"/nfts?size=2000")
    for nft in nfts:
      rc[nft["identifier"]]=(int(nft["balance"]) if "balance" in nft else 1)

    if not nft_addr is None:
      return rc[nft_addr] if nft_addr in rc else 0
    else:
      return rc




  def get_pem(self,secret_key: bytes, pubkey: bytes):
    name =Account(pubkey).address.bech32()

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
                     subject="Votre compte Elrond est disponible",
                     mail_new_wallet="",mail_existing_wallet="",
                     send_qrcode_with_mail=True,
                     histo:DAO=None,send_real_email=True) -> Key:
    """
    :param fund:
    :param name:
    :param seed_phrase:
    :return: Account, PEM,words,qrcode
    """
    if histo:
      pubkey=histo.get_address(email,self.network)
      if pubkey:
        log("Impossible de créer un deuxième compte pour cette adresse "+pubkey)
        _u = Account(address=pubkey)
        if send_real_email:
          url_explorer=self.getExplorer(pubkey,"accounts")
          send_mail(open_html_file(mail_existing_wallet,{
            "wallet_address":pubkey,
            "mini_wallet":self.nfluent_wallet_url(pubkey,domain_appli),
            "nfluent_wallet":self.nfluent_wallet_url(pubkey,domain_appli),
            "official_wallet":"https://xportal.com/",
            "url_explorer":url_explorer
          },domain_appli=domain_appli),email,subject=subject)
          return Key(address=_u.address.bech32(),name=email.split("@")[0],network="elrond")

    log("Création d'un nouveau compte")
    if len(seed) == 0:
      words=generate_mnemonic()
      qr=pyqrcode.create(words)
      buffered=io.BytesIO()
      qr.png(buffered,scale=5)
      qrcode=buffered.getvalue()
      secret_key, pubkey = derive_keys(words)

      address = Address(pubkey).bech32()
      _u=Account(address=address)
      _u.secret_key=secret_key.hex()
    else:
      qrcode=""
      secret_key, pubkey = derive_keys(seed)
      words=seed
      address = Address(pubkey).bech32()

    log("Création du compte "+self.getExplorer(Address(pubkey).bech32(),"address"))

    if len(email)>0:
      wallet_appli=self.nfluent_wallet_url(address,domain_appli)
      if not send_qrcode_with_mail:qrcode=None
      if send_real_email:
        url_explorer=self.getExplorer(address,"accounts")

        if send_mail(open_html_file(mail_new_wallet,{
          "wallet_address":address,
          "mini_wallet":wallet_appli,
          "url_wallet":self.getWallet(address),
          "url_explorer":url_explorer,
          "words":words,
          "qrcode":"cid:qrcode",
          "access_code":get_access_code_from_email(address)
        },domain_appli=domain_appli),email,subject=subject,attach=qrcode,filename="qrcode.png" if not qrcode is None else ""):
          if histo: histo.add_email(email,address,self.network)

    return Key(secret_key.hex(),name=email.split("@")[0],address=address,seed=words)


  def analyse_attributes(self,body,with_ipfs=True,timeout=2) -> (list,str,str):
    """
    analyse du champs attributes des NFT elrond (qui peut contenir les données onchain ou via IPFS)
    :param body:
    :return: les attributs, description, les tags
    """
    tags=""
    try:
      attr=str(base64.b64decode(bytes(body,"utf8")),"utf8")
    except:
      attr=str(base64.b64decode(body))

    #log("Pour les attributs, analyse de la chaine "+attr)

    if "tags:" in attr:
      tags=attr.split("tags:")[1].split(";")[0]

    #Analyse d'un fichier json d'attribut dans la description onchain
    if attr.startswith("{\""):attr=" - "+attr
    if " - {\"" in attr:
      desc=attr.split(" - {\"")[0]
      attr="{\""+attr.split(" - {\"")[1]
      _d=json.loads(attr)
      rc=[]
      for k in _d.keys():
        rc.append({"trait_type":k,"value":_d[k]})
      return rc,desc,tags

    if "metadata" in attr:
      cid=attr.split("metadata:")[1].split(";")[0]
      #log("Recherche des attributs via "+cid)
      cid=cid.split("/")[0]                                         #Au cas ou le nom du fichier aurait été ajouté dans le cid
      ipfs_url="https://ipfs.io/ipfs/"+cid
      result=api(ipfs_url,timeout=timeout) if with_ipfs else ipfs_url
      if result is None:result=dict()

      return result["attributes"] if "attributes" in result else "",\
             result["description"] if "description" in result else "",\
             tags

    return [],attr,tags


  def get_nft(self,token_id:str,attr=False,transactions=False,with_balance=None) -> NFT:
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

      item["attributes"],item["description"],item["tags"]=self.analyse_attributes(item["attributes"],True)

      nft=NFT(object=item)
      nft.network=self.network
      if with_balance:
        balances=api(url+"/accounts")
        if token_id in balances: nft.balance={with_balance:balances[token_id]}

      # if transactions:
      #   transactions=api(self._proxy.url+"/nfts/"+token_id+"/transactions","gateway=api")

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



  def get_nfts(self,_user:Account,limit=2000,with_attr=False,offset=0,with_collection=False,type_token="NonFungibleESDT,SemiFungibleESDT") -> [NFT]:
    """
    https://docs.multiversx.com/tokens/nft-tokens
    voir
    :param _user:
    :param limit:
    :param with_attr:
    :return:
    """
    _user=self.toAccount(_user)
    if _user is None:return []
    rc:[NFT]=[]
    owner=_user.address.bech32()
    balances=self.get_balances(_user.address)

    #nfts:dict=api(self._proxy.url+"/address/"+_user.address.bech32()+"/esdt")
    nfts=[]
    for type_t in type_token.split(","):
      if not type_t.endswith("ESDT"):type_t=type_t+"ESDT"
      result:list=api(self._proxy.url+"/accounts/"+owner+"/nfts?withSupply=true&type="+type_t+"&size="+str(limit))
      if result is None:
        log("Le compte "+owner+" n'existe pas")
        return []
      nfts=nfts+result

    #nfts=list(nfts["data"]["esdts"].values())
    if len(nfts)<offset:return []

    collections=dict()
    for nft in nfts[offset:limit]:
      if "attributes" in nft:
        _data={}
        nft["attributes"],nft["description"],nft["tags"]=self.analyse_attributes(nft["attributes"],with_attr)

        collection_id,nonce=self.extract_from_tokenid(nft["identifier"])
        if not collection_id in collections.keys():
          collections[collection_id]=self.get_collection(collection_id) if with_collection else {"id":collection_id}

        collection=collections[collection_id]
        if not "royalties" in nft or nft["royalties"]=="": nft["royalties"]=0
        nft["owner"]=_user.address.bech32()
        _nft=NFT(
          object=nft,
          collection=collection,
          creators=[{"address":nft["creator"],"share":int(nft["royalties"])/100}] if not "creators" in _data else _data["creators"],
        )
        _nft.balances={_user.address.bech32():balances[_nft.address] if _nft.address in balances else 0}
        _nft.network=self.network

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
    _user=self.toAccount(_user)
    collection_id,nonce=self.extract_from_tokenid(token_id)
    data = "freezeSingleNFT@" + str_to_hex(collection_id) \
           + "@" + int_to_hex(nonce,4) \
           + "@" + str_to_hex(_user.address.hex(), False)
    t = self.send_transaction(_user, Account(address=NETWORKS[self.network_type]["nft"]), _user, 0, data)
    return t


  def burn(self,_user,token_id):
    """
    https://docs.elrond.com/developers/nft-tokens/
    :param _user:
    :param token_id:
    :return:
    """
    _user=self.toAccount(_user)
    data = "ESDTLocalBurn@" + str_to_hex(token_id,False) + "@" + int_to_hex(1,4)
    t = self.send_transaction(_user,_user , _user, 0, data)
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
    t = self.send_transaction(_user, _user, _user, 0, data)
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



  def mint(self, miner:Key, title, description, collection:dict, properties: list,
           storage:str, files=[], quantity=1, royalties=0, visual="", tags="", creators=[],
           domain_server="",price=0,symbol="NFluentToken"):
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

    miner=self.toAccount(miner)

    if len(properties)>0 or len(tags)>0:
      _metadata={
        "name":title,
        "id":now("hex"),
        "description":description,
        "attributes":properties,
        "creators":creators,
        "price":str(price),
        "symbol":symbol
      }

      try:
        cid=storage.add(_metadata)
      except:
        return returnError("!Impossible de mettre les metadata en ligne sur le noeud IPFS propriétaire")

      log("Address des metadata: "+cid["url"])
      url_metadata=cid["url"]
      s="metadata:"+cid["cid"]
      if len(tags)>0: s=s+"tags:"+tags
      _h=hex(hash(s) & sys.maxsize).replace("0x","")
      if len(_h) % 2!=0: _h="0"+_h
    else:
      url_metadata=""
      s=description
      _h="00"

    #Traitement de la problématique des caractères spéciaux
    s=strip_accents(s.replace("\n"," "))
    title=strip_accents(title)
    log("tags et attributes : "+s)

    #hash = hex(int(now() * 1000)).upper().replace("0X", "")


    #Exemple de creation:
    #ESDTNFTCreate@4d41434f4c4c4543542d323565666366@01@4d6f6e546f6b656e@09c4@516d63636265345a78434b72706471587772784841377979347473635563465a4a6931724c69414d624d6a643252@746167733a3b6d657461646174613a516d5947397a6e724c7a735252594d436d6e52444a7931436f7478676e4a384b6a5668746870485a553775436d59@68747470733a2f2f697066732e696f2f697066732f516d63636265345a78434b72706471587772784841377979347473635563465a4a6931724c69414d624d6a643252

    method="ESDTNFTCreate" #if quantity==1 else "ESDTSFTCreate"
    data = method \
           + "@" + str_to_hex(collection["id"],False) \
           + "@" + int_to_hex(quantity,6) \
           + "@" + str_to_hex(title, False) \
           + "@" + int_to_hex(royalties*100,4) \
           + "@" + _h \
           + "@" + str_to_hex(s,False) \
           + "@" + str_to_hex(visual,False)

    if len(url_metadata)>0: data=data+ "@" + str_to_hex(url_metadata,False)

    for f in files:
      if len(f)>0:
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

    t = self.send_transaction(miner, miner, miner, 0, data)
    if "error" in t and len(t["error"])>0:
      return {"error":t["error"],"hash":""}

    if t["status"]!="success":
      return {
               "error":hex_to_str(str(base64.b64decode(t["logs"]["events"][0]["data"])).split("@")[1]),
               "hash":t["hash"],
                "explorer":self.getExplorer(t["hash"])
             }


    nonce = t["logs"]["events"][0]
    nonce = base64.b64decode(nonce["topics"][1]).hex()
    rc={
      "error":"",
      "tx":str(t["hash"]),
      "result":{"transaction":str(t["hash"]),"mint":collection["id"]+"-"+nonce},
      "balance":0,
      "link_mint":self.getExplorer(collection["id"]+"-"+nonce,"nfts"),
      "link_transaction":self.getExplorer(t["hash"]),
      "out":"",
      "cost":0,
      "unity":"EGLD",
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


  def toAccount(self, user):
    if type(user)==Key:
      _user=Account(address=user.address)
      _user.secret_key=user.secret_key
      return _user

    if type(user)==dict:
      if "address" in user:
        user=user["address"]
      else:
        if "address" in user:user=user["address"]

    if type(user)==str:
      if len(user)==0: return None

      if user.startswith("erd"):
        key=self.find_key(user)
        if key: user=key.name
      else:
        if len(user)>130:
          data=decrypt(user)
          if data.startswith("erd"):
            _user=Account(address=data)
          else:
            _user=Account(address=data[:16])
            _user.secret_key=data
          return _user


      if len(user.split(" "))>10:
        secret_key, pubkey = derive_keys(user.strip())
        user=Account(address=Address(pubkey).bech32())
        user.secret_key=secret_key.hex()
        return user

      if user.startswith("erd"):
        user=Account(address=user)
      else:
        pem_file=ELROND_KEY_DIR+user+(".pem" if not user.endswith('.pem') else '')
        if exists(pem_file):
          with open(pem_file,"r") as file:
            txt=file.read()
            if txt.startswith("-----BEGIN PRIVATE KEY"):
              user=Account(pem_file=pem_file)
            else:
              words=""
              for s in txt.split("\n "):
                if len(s)>1:
                  if " " in s:
                    words=words+s.split(" ")[1]+" "
                  else:
                    words=words+s
              words=words.replace("\n","").strip()
              secret_key, pubkey = derive_keys(words)
              user=Account(address=Address(pubkey).bech32())
              user.secret_key=secret_key.hex()
        else:
          return None

    return user



  def extract_from_tokenid(self, token_id):
    nonce=""
    collection_id=""

    l_fields=len(token_id.split("-"))
    if l_fields>1:
      collection_id=token_id.split("-")[0]+"-"+token_id.split("-")[1]
    if l_fields>2:
      nonce=token_id.split("-")[2]

    return collection_id,nonce


  def balance(self,account:Account):
    if type(account)!=Account: account=self.toAccount(account)
    return self._proxy.get_account_balance(account.address)/1e18



  def get_keys(self,qrcode_scale=0,address="") -> [Key]:
    """
    retourne l'ensemble des clé ou une seul filtré par l'adresse ou le nom
    :param qrcode_scale:
    :param with_balance:
    :param address:
    :return:
    """
    rc=[]
    log("Lecture des clés "+str(listdir(ELROND_KEY_DIR)))
    for f in listdir(ELROND_KEY_DIR)+self.keys:
      name=""
      secret_key=""

      if f.endswith(".pem"): #or f.endswith(".json"):
        acc=Account(pem_file=ELROND_KEY_DIR+f)
        secret_key=acc.secret_key
        name=f.replace(".pem","").replace(".json","")

        if len(address)==0 or (name==address or acc.address.bech32()==address):
          k=Key(name=name,address=acc.address.bech32(),secret_key=secret_key,network="elrond")
          rc.append(k)

    return rc


  def find_key(self,address_or_name) -> Key:
    if type(address_or_name)==Account:
      address_or_name=address_or_name.address.bech32()

    for k in self.get_keys():
      if k.address==address_or_name or k.name==address_or_name:
        return k

    return None

  def get_owners_of_nft(self, nft_addr:str) -> [NfluentAccount]:
    """
    voir https://devnet-api.multiversx.com
    :param address:
    :return:
    """
    result=api(self._proxy.url+"/nfts/"+nft_addr+"/accounts")
    rc=[NfluentAccount(address=x["address"]) for x in result]
    return rc

