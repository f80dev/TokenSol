import base64
import io
from os import listdir,remove
from os.path import exists
import requests
import pyqrcode
from Tools import get_qrcode

import textwrap
from secret import ELROND_PASSWORD
from nftstorage import NFTStorage
from Tools import int_to_hex, str_to_hex, log, api,send_mail,open_html_file
from ipfs import IPFS
from erdpy import config
from erdpy.wallet.core import generate_mnemonic
from erdpy.proxy import ElrondProxy
from erdpy.transactions import Transaction
from erdpy.accounts import Account,Address
from erdpy.wallet import derive_keys
from PIL import Image,ImageSequence


RESULT_SECTION="smartContractResults"
LIMIT_GAS=200000000
PRICE_FOR_STANDARD_NFT=50000000000000000
ELROND_KEY_DIR="./Elrond/PEM/"


NETWORKS={
  "testnet":{
    "unity":"xEgld",
    "faucet":"https://r3d4.fr/elrond/testnet/index.php",
    "proxy":"https://testnet-gateway.elrond.com",
    "explorer":"https://testnet-explorer.elrond.com",
    "wallet":"http://testnet-wallet.elrond.com",
    "nft":"erd1qqqqqqqqqqqqqqqpqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqzllls8a5w6u",
    "shard":0
  },

  #erd1qqqqqqqqqqqqqpgqkwfvpkaf6vnn89508l0gdcx26vpu8eq5d8ssz3lhlf
  "devnet":{
    "unity":"xEgld",
    "identifier":"TFE-116a67",
    "faucet":"https://r3d4.fr/elrond/devnet/index.php",
    "proxy":"https://devnet-api.elrond.com",
    "explorer":"https://devnet-explorer.elrond.com",
    "wallet":"https://devnet-wallet.elrond.com",
    "nft":"erd1qqqqqqqqqqqqqqqpqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqzllls8a5w6u",
    "shard": 1
  },

  "mainnet":{
    "unity":"Egld",
    "identifier":"",
    "faucet":"",
    "proxy":"https://api.elrond.com",
    "explorer":"https://explorer.elrond.com",
    "wallet":"https://wallet.elrond.com",
    "nft":"erd1qqqqqqqqqqqqqqqpqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqzllls8a5w6u",
    "shard": 1
  }
}


class Elrond:
  def __init__(self,network="elrond_devnet"):
    self.network_name="devnet" if "devnet" in network else "mainnet"
    self._proxy=ElrondProxy(NETWORKS[self.network_name]["proxy"])




  def getExplorer(self, tx, type="transactions"):
    url = NETWORKS[self.network_name]["explorer"] + "/" + type + "/" + tx
    url=url.replace("api","explorer")
    if "elrond.com" in self._proxy.url:
      return url
    else:
      type = type.replace("transactions", "transaction")
      return self._proxy.url + "/" + type + "/" + tx




  def send_transaction(self, _sender: Account,
                       _receiver: Account,
                       _sign: Account,
                       value: str, data: str,
                       gas_limit=LIMIT_GAS, timeout=60):
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

      #tr = self.wait_transaction(tx, not_equal="pending")
      return tx.raw
    except Exception as inst:
      log("Exception d'execution de la requete " + str(inst.args))
      return None


  def get_collections(self,creator:Account,fields=list()):
    creator=self.toAccount(creator)
    if type(creator)==str:creator=Account(address=creator)
    url=self._proxy.url+"/collections?creator="+creator.address.bech32()
    rc=list()
    cols=api(url,"api=gateway")
    if len(fields)>0:
      for col in cols:
        rc.append(col[fields])
    else:
      rc=cols

    return rc


  def format_offchain(self,_data) -> dict:
    keys=self.get_keys()
    for c in _data["properties"]["creators"]:
      for k in keys:
        if k["name"]==c["address"]:
          c["address"]=k["pubkey"]

    return {
      "properties":{
        "attributes":_data["attributes"],
        "description":_data["description"],
        "collection":_data["collection"]["name"],
        "creators":_data["properties"]["creators"]
      },
      "files":_data["properties"]["files"]
    }





  def transfer(self,collection_id,nonce,_from:Account,_to:Account):
    """
    Transfert d'un NFT
    voir
    :param collection_id:
    :param nonce:
    :param _from:
    :param _to:
    :return:
    """
    _from=self.toAccount(_from)
    _to=self.toAccount(_to)
    if _from.address.bech32()==_to.address.bech32(): return False

    log("Transfert de "+collection_id+"-"+nonce+" de "+_from.address.bech32()+" a "+_to.address.bech32())
    data = "ESDTNFTTransfer@" + str_to_hex(collection_id,False) \
           + "@" + nonce \
           + "@" + int_to_hex(1) \
           + "@" + _to.address.hex()
    t = self.send_transaction(_from, _from, _from, 0, data)
    return t




  def add_collection(self, owner:Account, collection,type="SemiFungible"):
    """
    gestion des collections sur Elrond
    voir
    :param owner:
    :param collection:
    :param collection_id:
    :param type:
    :return:
    """
    owner=self.toAccount(owner)
    collection:str=collection.replace(" ","").replace("'","")[:20]
    if collection.lower().startswith("elrond"):
      log("La collection en doit pas commencer par Elrond")
      return None

    collection_id=None
    for col in self.get_collections(owner):
      if col["name"]==collection:
        collection_id=str_to_hex(col["collection"],False)
        break

    if collection_id is None:
      collection_id=collection[:8].upper() if collection_id is None else collection_id
      #Exemple de requete : issueNonFungible@4d61436f6c6c656374696f6e456c726f6e64@4d41434f4c4c4543@63616e467265657a65@74727565
      #Résultat : https://devnet-explorer.elrond.com/transactions/1e7ac5f911cffce2b846c3f98b8abad636b2958a32df6bebde0ee0b83f087a94
      data = "issue"+type \
             + "@" + str_to_hex(collection, False) \
             + "@" + str_to_hex(collection_id, False) \
             + "@" + str_to_hex("canFreeze", False)+"@"+str_to_hex("true",False) \
             + "@" + str_to_hex("canChangeOwner", False)+"@"+str_to_hex("true",False) \
             + "@" + str_to_hex("canUpgrade", False)+"@"+str_to_hex("true",False) \
             + "@" + str_to_hex("canWipe", False)+"@"+str_to_hex("true",False) \
             + "@" + str_to_hex("canTransferNFTCreateRole", False)+"@"+str_to_hex("true",False) \
             + "@" + str_to_hex("canPause", False)+"@"+str_to_hex("true",False) \
             + "@" + str_to_hex("canAddSpecialRoles", False)+"@"+str_to_hex("true",False)

      t = self.send_transaction(owner,
                                Account(address=NETWORKS[self.network_name]["nft"]),
                                owner,
                                PRICE_FOR_STANDARD_NFT,
                                data)

      if t is None:
        log("BUG: consulter "+self.getExplorer(owner.address.bech32(),"address"))
        return None

      if RESULT_SECTION in t and len(t[RESULT_SECTION][0]["data"].split("@")) > 2:
        collection_id = t[RESULT_SECTION][0]["data"].split("@")[2]

        data = "setSpecialRole@" + collection_id + "@" + owner.address.hex() \
               + "@" + str_to_hex("ESDTRoleNFTCreate",False) \
               + "@" + str_to_hex("ESDTRoleNFTUpdateAttributes",False)

        #TODO pour l'instant ne fonctionne pas
        #data=data+ "@" + str_to_hex("ESDTRoleLocalBurn",False);

        if type=="SemiFungible": data=data + "@" + str_to_hex("ESDTRoleNFTAddQuantity", False)

        #Exemple d'usage de setSpecialRole sur la collection présente
        #setSpecialRole@43414c5649323032322d356364623263@b13a017423c366caff8cecfb77a12610a130f4888134122c7937feae0d6d7d17@45534454526f6c654e4654437265617465@45534454526f6c654e46544164645175616e74697479

        t = self.send_transaction(owner,
                                  Account(address=NETWORKS[self.network_name]["nft"]),
                                  owner, 0, data)

      else:
        log("Erreur de création de la collection. Consulter "+self.getExplorer(owner.address.bech32(),"address"))
        collection_id=None

    return collection_id


  def get_account(self,_user):
    _user=self.toAccount(_user)
    rc=self._proxy.get_account(_user.address)
    rc["amount"]=int(rc["balance"])/1e18
    return rc



  def get_pem(self,secret_key: bytes, pubkey: bytes):
    name = pubkey.hex()

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



  def create_account(self,email="",seed="",network="elrond-devnet"):
    """
    :param fund:
    :param name:
    :param seed_phrase:
    :return:
    """
    log("Création d'un nouveau compte")

    if len(seed) == 0:
      words=generate_mnemonic()

      qr=pyqrcode.create(words)
      buffered=io.BytesIO()
      qr.png(buffered,scale=5)
      qrcode=buffered.getvalue()

      secret_key, pubkey = derive_keys(words)

      #secret_key, pubkey = generate_pair()
      address = Address(pubkey).bech32()
      _u=Account(address=address)
      _u.secret_key=secret_key.hex()
    else:
      qrcode=""
      secret_key, pubkey = derive_keys(seed)
      words=seed
      address = Address(pubkey).bech32()
      _u = Account(address=address)
      _u.secret_key=secret_key.hex()

    log("Création du compte "+self.getExplorer(Address(pubkey).bech32(),"address"))

    if len(email)>0:
      send_mail(open_html_file("mail_new_account",{
        "wallet_address":address,
        "url_wallet":"https://wallet.elrond.com" if "mainnet" in network else "https://devnet-wallet.elrond.com",
        "words":words,
        "qrcode":"cid:qrcode"
      }),email,subject="Votre compte Elrond est disponible" ,attach=qrcode,filename="qrcode.png")

    return _u, self.get_pem(secret_key,pubkey),words,qrcode




  def get_nfts(self,_user:Account,limit=20):
    _user=self.toAccount(_user)
    rc=list()
    nfts:dict=api(self._proxy.url+"/address/"+_user.address.bech32()+"/esdt")
    if nfts:
      for nft in list(nfts["data"]["esdts"].values()):
        if "attributes" in nft:
          log("Analyse de "+str(nft))
          nft["attributes"]=str(base64.b64decode(nft["attributes"]),"utf8")
          nft["tags"]=nft["attributes"].split("tags:")[1].split(";")[0]
          cid=nft["attributes"].split("metadata:")[1].split("/")[0]
          _data=requests.get("https://ipfs.io/ipfs/"+cid).json()
          collection=nft["tokenIdentifier"].replace("-"+nft["tokenIdentifier"].split("-")[2],"")
          nft["metadataOffchain"]={
            "attributes":_data["attributes"],
            "collection":{"name":_data["collection"]},
            "image":str(base64.b64decode(nft["uris"][0]),"utf8")
          }
          nft["id"]=nft["tokenIdentifier"]
          nft["address"]=nft["tokenIdentifier"]
          nft["network"]="elrond-"+self.network_name
          nft["accountInfo"]={"mint":_user.address.bech32()}
          nft["splTokenInfo"]={"owner":_user.address.bech32(),"amount":int(nft["balance"])}

          nft["metadataOnchain"]={
            "updateAuthority":[],
            "data":{
              "creators":[{"address":nft["creator"],"share":int(nft["royalties"])/100}] if not "creators" in _data else _data["creators"],
              "name":nft["name"],
              "symbol":nft["tokenIdentifier"].split("-")[1]
            }
          }
          for role in self.getRoleForToken(collection):
            if "ESDTRoleNFTUpdateAttributes" in role["roles"]:nft["metadataOnchain"]["updateAuthority"].append(role["account"])
          nft["metadataOnchain"]["updateAuthority"]=",".join(nft["metadataOnchain"]["updateAuthority"])


          rc.append(nft)
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
    t = self.send_transaction(_user, Account(address=NETWORKS[self.network_name]["nft"]), _user, 0, data)
    return t


  def burn(self,_user,token_id):
    """
    https://docs.elrond.com/developers/nft-tokens/
    :param _user:
    :param token_id:
    :return:
    """
    _user=self.toAccount(_user)
    collection_id,nonce=self.extract_from_tokenid(token_id)
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








  def mint(self, miner, title, collection, properties: dict,ipfs:IPFS,files=[], quantity=1, royalties=0, visual="", file="", tags=""):
    """
    Fabriquer un NFT au standard elrond
    https://docs.elrond.com/developers/nft-tokens/
    :type ipfs: object
    :param contract:
    :param user_from:
    :param arguments:
    :return:
    """

    if collection is None:return None,None
    miner=self.toAccount(miner)

    #hash = hex(int(now() * 1000)).upper().replace("0X", "")
    hash="00"

    # for col in self.get_collections(user_from,[]):
    #     if col["name"]==collection:
    #         collection_id=col["ticker"]
    #         break

    # if collection_id=="":
    #     token_id=self.add_collection(user_from,collection)

    #Voir https://docs.elrond.com/developers/nft-tokens/
    #exemple de creation d'une collection de SFT
    # Name=CalviOnTheRock collection=Calvi2022
    # TransferCreateRole
    #Résultat issueSemiFungible@43616c76694f6e546865526f636b32303232@43414c564932303232@63616e5472616e736665724e4654437265617465526f6c65@74727565
    #Création de billet
    #Exemple : issueSemiFungible@546f757245696666656c@544f555245494646454c@63616e467265657a65@74727565@63616e57697065@74727565@63616e5472616e736665724e4654437265617465526f6c65@74727565
    #Transaction hash 3f002652038ba8aed2876809a9e019451770c740749c1047a5b4d354f5fb217a

    if visual.lower().endswith("webp"):
      visual=convert_to_gif(visual,NFTStorage())

    cid_metadata=ipfs.add(properties)
    nonce="02"
    s="metadata:"+cid_metadata["Hash"]+"/props.json;tags:"+("" if len(tags)==0 else " ".join(tags))

    data = "ESDTNFTCreate@" + collection \
           + "@" + int_to_hex(quantity,2) \
           + "@" + str_to_hex(title, False) \
           + "@" + int_to_hex(royalties*100,4) \
           + "@" + hash \
           + "@" + str_to_hex(s,False) \
           + "@" + str_to_hex(visual,False) \
           + "@" + str_to_hex(cid_metadata["url"],False)

    for f in files:
      filename=f["files"]
      if filename.lower().endswith(".webp"):filename=convert_to_gif(filename,NFTStorage())
      data=data+"@"+str_to_hex(filename,False)

    #Exemple de minage: ESDTNFTCreate@544f5552454946462d323864383938@0a@4c6120746f75722071756920636c69676e6f7465@09c4@516d64756e4a7a71377850443164355945415a6952647a34486d4d32366179414d574334687a63785a447735426b@746167733a3b6d657461646174613a516d54713845666d36416634616a35383847694d716b4d44524c475658794133773439315052464e413471546165@68747470733a2f2f697066732e696f2f697066732f516d64756e4a7a71377850443164355945415a6952647a34486d4d32366179414d574334687a63785a447735426b

    if len(file)>0:
      data=data+"@"+str_to_hex(file)

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
    if t is None: return None

    if "logs" in t:
      nonce = t["logs"]["events"][0]
      nonce = int_to_hex(base64.b64decode(nonce["topics"][1])[0],2)

    return nonce,cid_metadata


  def getRoleForToken(self,collection):
    payload={
      "scAddress":NETWORKS[self.network_name]["nft"],
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
    if type(user)==str:
      if user.startswith("erd"):
        user=Account(address=user)
      else:
        pem_file="./Elrond/PEM/"+user+(".pem" if not user.endswith('.pem') else '')
        if exists(pem_file):
          with open(pem_file,"r") as file:
            txt="".join(file.readlines())
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
          keystore_file="./Elrond/PEM/"+user+(".json" if not user.endswith('.json') else '')
          pass_file="./Elrond/PEM/"+user+"_pass"
          if not exists(pass_file):
            f=open(pass_file,"w")
            f.writelines(ELROND_PASSWORD)
            f.close()
          user=Account(key_file=keystore_file,pass_file=pass_file)
          remove(pass_file)

    return user



  def extract_from_tokenid(self, token_id):
    collection_id=token_id.split("-")[0]+"-"+token_id.split("-")[1]
    nonce=token_id.split("-")[2]
    return collection_id,nonce


  def balance(self,account:Account):
    return self._proxy.get_account_balance(account.address)

  def get_keys(self,with_qrcode=False):
    rc=[]
    for f in listdir(ELROND_KEY_DIR):
      log("Lecture de "+f)
      if f.endswith(".pem") or f.endswith(".json"):
        _a=self.toAccount(f)
        rc.append({
          "name":f.replace(".pem","").replace(".json",""),
          "pubkey":_a.address.bech32(),
          "qrcode": get_qrcode(_a.address.bech32()) if with_qrcode else "",
          "explorer":self.getExplorer(_a.address.bech32(),"address"),
          "balance":self.balance(_a)/1e18,
          "unity":"egld"
        })

    return rc

