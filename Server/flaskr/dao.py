import base64
import hashlib
from random import randint

import requests
from bson import ObjectId
from pymongo import database, MongoClient, mongo_client

from flaskr.Keys import Key
from flaskr.NFT import NFT
from flaskr.NFluentAccount import NfluentAccount
from flaskr.Network import Network
from flaskr.Storage import Storage
from flaskr.Tools import log, now, get_hash, encrypt, simplify_email, is_email
from flaskr.secret import MONGO_INITDB_ROOT_USERNAME, MONGO_INITDB_ROOT_PASSWORD, MONGO_CLUSTER_CONNECTION_STRING, MONGO_WEB3_CONNECTION_STRING

#Voir les infos de connections du cloud sur
#Localisation de l'offre cloud :
from flaskr.settings import ENCODING_LENGTH_FOR_EMAIL

DB_SERVERS=dict(
  {
    "local":"mongodb://127.0.0.1:27017",
    "server":"mongodb://"+MONGO_INITDB_ROOT_USERNAME+":"+MONGO_INITDB_ROOT_PASSWORD+"@109.205.183.200:27017",
    "cloud":MONGO_CLUSTER_CONNECTION_STRING,
    "web3":MONGO_WEB3_CONNECTION_STRING
  }
)

DB_PREFIX_ID="db_"

class DAO(Storage,Network):
  db:database=None
  url:str=""

  def __init__(self,domain:str="server",dbname="nfluent",ope=None,config=None,network="",domain_server="",cid=""):
    Storage.__init__(self,domain_server)
    if network.startswith("dao"):network="db"+network[3:]
    Network.__init__(self,network=network)

    if ope and "database" in ope:
      self.domain=ope["database"]["connexion"]
      self.dbname=ope["database"]["dbname"]
    else:
      if config and "DB_SERVER" in config and "DB_NAME" in config:
        if config["DB_SERVER"] in DB_SERVERS:config["DB_SERVER"]=DB_SERVERS[config["DB_SERVER"]]
        self.dbname=config["DB_NAME"]
        self.domain=config["DB_SERVER"]
      else:
        if len(cid)>0:
          cid=str(base64.b64decode(cid[3:]),"utf8")
          network=cid.split("/")[0]

        if len(network)>0 and len(network.split("-"))>2:
          self.domain=network.split("-")[1]
          self.dbname=network.split("-")[2]
        else:

          if domain and dbname:
            self.dbname=dbname if not "-" in domain else domain.split("-")[2]
            self.domain=domain if not "-" in domain else domain.split("-")[1]

    #log("Initialisation de la base de données "+self.domain+"/"+self.dbname)
    if not self.connect(self.domain,self.dbname):
      log("connexion impossible a "+self.domain)


  def isConnected(self) -> bool:
    return not self.db is None

  #________________________________________liste des méthodes pour le storage

  def get(self, id,table="storage"):
    id=str(base64.b64decode(id[3:]),"utf8").split("/")[0]
    rc=self.db[table].find_one(filter={"Hash":id})
    if not rc is None:
      return rc["data"]

    return rc

  def getExplorer(self,addr="",type="address") -> str:
    return ""


  def add(self,content,overwrite=True) -> dict:
    if type(content)==str:
      if content.startswith("http"):
        content=requests.get(content).content

    to_save={"data":content}
    to_save["Hash"]=get_hash(content)

    self.add_data(to_save)
    id=to_save["Hash"]+"/db-"+self.domain+"-"+self.dbname

    id="db_"+str(base64.b64encode(bytes(id,"utf8")),"utf8")
    rc={"cid":id,"hash":get_hash(content)}
    if self.domain_server: rc["url"]=self.domain_server+"api/files/"+str(id)
    return rc

  def get_unity(self):
    return "dbcoin"




  def rem(self,key):
    key=str(base64.b64decode(key[3:]),"utf8").split("/")[0]
    rc=self.db["storage"].delete_one({"Hash":key})
    return rc.deleted_count==1

  def connect(self, domain, name):
    """
    effectue la connexion à la base si nécéssaire
    :param domain:
    :param name:
    :return:
    """
    if domain==self.domain and name==self.dbname and not self.db is None:
      return True

    self.url=DB_SERVERS[self.domain] if self.domain in DB_SERVERS else self.domain
    self.url=self.url.replace("rootpassword",MONGO_INITDB_ROOT_PASSWORD)
    #log("Tentative de connexion sur la base de données "+self.dbname+" sur "+self.url)
    try:
      self.db: mongo_client = MongoClient(self.url)[self.dbname]
      return self.db.list_collections().alive
    except Exception as inst:
      log("Base de données non disponible "+str(inst.args))
      self.db=None

    return False


  def get_keys(self,qrcode_scale=0,with_balance=False,with_account=False,with_secretKey=False,address="") -> [Key]:
    """
    retourne l'ensemble des clés public/privées du réseau
    :param qrcode_scale:
    :param with_balance:
    :param with_account:
    :param with_secretKey:
    :param address:
    :return:
    """
    rc=[]
    for obj in self.db["keys"].find():
      del obj["_id"]
      key=Key(obj=obj)
      rc.append(key)
    return rc

  def delete_key(self,key) -> bool:
    rc=self.db["keys"].delete_one({"address":key.address})
    return rc.deleted_count==1




  def get_nfts_from_collections(self,collections:[str],with_attr=False,format="class"):
    rc=[]
    for col in collections:
      for nft in list(self.db["nfts"].find({"collection":col})):
        del nft["_id"]
        _nft=NFT(object=nft)
        if format=="json":_nft=_nft.__dict__
        rc.append(_nft)

    return rc

  def get_nfts(self,addr:str=None,limit=2000,with_attr=False,offset=0,with_collection=False) -> [NFT]:
    rc=[]

    nfts=list(self.db["nfts"].find({"owner":addr}) if not addr is None else self.db["nfts"].find())

    if len(nfts)<offset: return []
    for nft in nfts[offset:offset+limit]:
      rc.append(NFT(object=nft))
    return rc


  def mint(self, miner, title, description, collection:dict, properties: list,
           storage:str, files=[], quantity=1, royalties=0, visual="", tags="", creators=[],
           domain_server="",price=0,symbol="NFluentToken",simulation=False):
    """
    Opere un transfert du NFT dans la base de données
    :param _data:
    :param ope:
    :param server_addr:
    :param id:
    :return:
    """
    nft=NFT(name=title,
            miner=miner.address,
            owner=miner.address,
            collection=collection["id"],
            attributes=properties,
            description=description,
            tags=tags,
            visual=visual,
            creators=creators,
            symbol=symbol,
            royalties=royalties,
            supply=quantity,
            price=price,
            files=files,
            dtCreate=now("dec"),
            balances={miner.address:quantity}
            )

    nft.address="db_"+now("hex")[2:]+"/db-"+self.domain+"-"+self.dbname     #l'addresse commençant par db_ permet de désigner une base de données
    nft.network="db-"+self.domain+"-"+self.dbname

    result=self.save_nft(nft)

    self.add_nft_to_account(miner.address,nft,nft.supply)

    rc={
      "error":"",
      "tx":"",
      "result":{"transaction":str(result.upserted_id),"mint":nft.address},
      "balance":0,
      "link_mint":"",
      "link_transaction":"",
      "out":"",
      "cost":0,
      "unity":"$",
      "command":"insert"
    }
    return rc

  def nfts_from_collection(self, col):
    rc=[]
    if col:
      nfts=self.db["nfts"].find(filter={"collection.id":col})
    else:
      nfts=self.db["nfts"].find()

    for nft in nfts:
      _nft=NFT(object=nft)
      rc.append(_nft)

    return rc


  def reset(self,item="all"):
    if item=="all":
      self.db["nfts"].drop()
      self.db["keys"].drop()
      self.db["accounts"].drop()
    else:
      self.db[item].drop()


  def delete(self, id):
    return self.db["nfts"].delete_one(filter={"id":id})


  def add_collection(self, owner:Key, collection_name:str,options:list=[],type_collection="SemiFungible",simulation=False) -> (dict):
    col={"owner":owner.address,"name":collection_name,"type":type_collection}
    if not self.db["collections"].find_one({"name":collection_name}) is None: return None
    if not simulation:
        rc=self.db["collections"].insert_one(col)
        col["id"]="col_"+str(rc.inserted_id)
    else:
      col["id"]=0
    return col


  def get_collection(self,collection_id):
    return self.db["collections"].find_one({"id":collection_id})

  def add_data(self, data):
    if type(data)==str:data=base64.b64decode(data)
    if type(data)==bytes:data={"content":data}
    rc=self.db["storage"].insert_one(data)
    return str(rc.inserted_id)

  def get_collections(self,owner_or_collection:str,detail:bool=False,type_collection="",special_role=""):
    rc=[]
    cols=self.db["collections"].find({"_id":ObjectId(owner_or_collection.replace("col_",""))}) if owner_or_collection.startswith("col") else self.db["collections"].find({"owner":owner_or_collection})
    for col in cols:
      if not "id" in col: col["id"]="col_"+str(col["_id"])
      del col["_id"]
      rc.append(col)

    return rc

    # if "nfts" in self.db.list_collection_names():
    #   for nft in self.db["nfts"].find():
    #     _nft=NFT(object=nft)
    #     if _nft.owner==owner or _nft.owner=="":
    #       if _nft.collection and _nft.collection not in rc: rc.append(_nft.collection)
    # return rc

  # def get_data(self, id):
  #   """
  #   recherche d'information dans l'espace de stockage
  #   :param id:
  #   :return:
  #   """
  #   if id.startswith("db_"):id=id[3:]
  #   return self.db["storage"].find_one(filter={"_id":ObjectId(id)})

  def add_histo(self, command,addr,transaction_id,ope="", collection_id="",network="",comment="",params=list()):
    if not self.db is None:
      self.db["histo"].insert_one({
        "operation":ope,
        "command":command,
        "addr":addr,
        "collection":collection_id,
        "ts":now(),
        "transaction":transaction_id,
        "network":network,
        "comment":comment,
        "params":params
      })

  def get_account(self,addr:str) -> NfluentAccount:
    if is_email(addr): addr=DB_PREFIX_ID + get_hash(addr)
    obj=self.db["accounts"].find_one({"address":addr})
    if obj is None: return None
    return NfluentAccount(obj=obj)

  def update_quantity(self, address:str,variation:int):
    """
    Mise a jour de la quantité
    :param _data:
    :param field:
    :return:
    """
    nft=self.db["nfts"].find_one({"address":address})
    if nft:
      nft["marketplace"]["quantity"]=nft["marketplace"]["quantity"]+variation
      self.db["nfts"].update_one({"address":address},{ "$set": { "marketplace": nft["marketplace"] } })
      return True
    else:
      return False





  def transfer(self,nft_addr:str,_from:Key,to_addr:str):
    """
    correspond à un changement d'address
    :param nft_addr:
    :param to_addr:
    :return:
    """
    nft=self.get_nft(nft_addr)
    if nft:
      if nft.owner!=_from.address: raise RuntimeError(str(_from)+" n'est pas le propriétaire de "+str(nft))
      rc=self.db["nfts"].update_one({"address":nft.address},{"$set":{"owner":to_addr}})
      if rc.modified_count==1: return self.create_transaction()

    return self.create_transaction(error="transfert annulé")


  def create_account(self,email="",seed="",domain_appli="",
                     subject="Votre nouveau wallet est disponible",
                     mail_new_wallet="",mail_existing_wallet="",
                     send_qrcode_with_mail=True,dictionnary=dict(),
                     histo=None,send_real_email=True,solde=100) -> Key:
    name=email.split("@")[0]
    addr= DB_PREFIX_ID + get_hash(email)
    key=self.db["keys"].find_one({"address":addr})
    if key is None:
      for i in range(12): seed=seed+str(now("hex"))+" "
      key=Key("privatekey_"+addr,name,addr,"db-"+self.domain+"-"+self.dbname,seed)
      self.db["keys"].insert_one(key.__dict__) #Dans le cas d'une simulation de blockchain, la
    else:
      key=Key(obj=key)

    if self.get_account(key.address) is None:
      acc=NfluentAccount(address=key.address,network=self.network,balance=solde)
      self.db["accounts"].insert_one(acc.__dict__) #Dans le cas d'une simulation de blockchain, la

    return key



  def burn(self,nft_addr:str,miner:Key,quantity=1):
    _miner=self.get_account(miner.address)
    if _miner is None: return False

    if not nft_addr in _miner.nfts_balances or _miner.nfts_balances[nft_addr]<quantity:
      return self.create_transaction(error="Quantité insuffisante",hash="db_"+now("hex"),nft_addr=nft_addr)

    _miner.nfts_balances[nft_addr]=_miner.nfts_balances[nft_addr]-quantity

    self.save_account(_miner)

    return self.create_transaction(error="",hash="db_"+now("hex"),nft_addr=nft_addr)






  def registration(self,email,perms,force=False):
    """
    Enregistrement d'un compte dans la table des utilisateurs de l'appli
    :param email:
    :param perms:
    :param force:
    :return:
    """
    obj=self.db["users"].find_one({"email":encrypt(email,short_code=ENCODING_LENGTH_FOR_EMAIL)})
    if not obj is None and not force:
      obj["message"]="already exists"
    else:
      access_code=str(randint(100000,999999))
      obj={
        "email":encrypt(email,short_code=ENCODING_LENGTH_FOR_EMAIL),
        "alias":email.split("@")[0],
        "routes":[],
        "perms":perms,
        "access_code":access_code,
        "message":"account created"
      }
      rc=self.db["users"].insert_one(obj)

    del obj["_id"]
    return obj

  def get_user(self, email,access_code,network_for_keys=""):
    if email is None or access_code is None:return None
    user=self.db["users"].find_one({"email":encrypt(email,short_code=ENCODING_LENGTH_FOR_EMAIL),"access_code":access_code})
    if user:
      del user["_id"]
      if not "keys" in user: user["keys"]=dict()
      if len(network_for_keys)>0:
        if not network_for_keys in user["keys"]:user["keys"][network_for_keys]=list()

      user["access_code"]=access_code
      return user
    log("Aucun utilisateur trouver")
    return None

  def toAddress(self,secret_key:str):
    return secret_key.replace("privatekey_","")

  def add_email(self,email:str,addr:str,network:str):
    """
    sauvegarde de l'adresse du wallet en fonction d'un cryptage de l'adresse email
    :param email:
    :param addr:
    :param network:
    :return:
    """
    network=network.split("-")[0]
    encoded_email=hashlib.sha256(email.encode()).hexdigest()
    self.db["account_settings"].insert_one({
      "email":encoded_email,
      "address":addr,
      "network":network
    })

  def get_address(self,email:str,network:str):
    network=network.split("-")[0]
    encoded_email=hashlib.sha256(email.encode()).hexdigest()
    rc=self.db["account_settings"].find_one({"email":encoded_email,"network":network})
    if rc:return rc["address"]
    return rc



  def add_validator(self, id,ask_for):
    """
    Ajout d'un nouveau validateur dans la liste
    :param ask_for contient une collection ou une liste de NFT
    :return:
    """
    if ask_for is None or len(ask_for)==0:
      log("Inscription rejetée car aucune demande de collection ou d'opération associée")
      return False

    self.db["validators"].update_one({"id":id},{"$set":{
      "id":id,
      "dtStart":now(),
      "ask":ask_for,
      "user":"",
      "nfts":0
    }
    },upsert=True)
    return True



  def get_nft(self, nft_addr,attr=True):
    return NFT(object=self.db["nfts"].find_one({"address":nft_addr}))

  def add_key_to_user(self, email,access_code, network, secret_key,name=""):
    """
    Ajoute une clé à un profil dans la base
    :param access_code:
    :param network:
    :param key:
    :param name:
    :return:
    """
    if access_code is None:return False
    network=network.split("-")[0]
    user=self.get_user(email,access_code,network)
    if user:
      k=Key(name=name,secret_key=secret_key,network=network)
      if not k in user["keys"][network]:
        user["keys"][network].append(k.__dict__)
        rc=self.db["users"].update_one({"email":user["email"]},update={"$set":{"keys":user["keys"]}})
        return rc.modified_count==1
      else:
        return False

    return False

  def delete_user(self, email,access_code):
    if access_code is None:return False
    user=self.get_user(email,access_code)
    if user:
      log("Suppression de "+email)
      rc=self.db["users"].delete_one({"email":user["email"],"access_code":user["access_code"]})
      return rc.deleted_count==1
    else:
      log("Impossible de supprimer "+user+" inexistant ou access_code incorrect")
    return False

  def set_access_code(self, email,access_code, new_access_code):
    user=self.get_user(email,access_code)
    if user:
      rc=self.db["users"].update_one({"email":user["email"]},{"$set":{"access_code":new_access_code}})
      if rc.modified_count==1: return True
    return False

  def get_docs(self, user,type_doc="operation") -> list:
    if user is None: return []
    rc=list()
    for x in self.db["docs"].find({"type_doc":type_doc,"user":user}):
      del x["_id"]
      rc.append(x)
    return rc

  def add_doc(self, doc, user,id_doc="", type_doc="operation"):
    if len(user)==0: return False
    if len(id_doc)==0: id_doc=doc["id"]
    if self.db["docs"].find({"id":id_doc,"type_doc":type_doc,"user":user}) is None:
      rc=self.db["docs"].insert_one({"type_doc":type_doc,"user":user,"doc":doc,"id":id_doc})
      return rc.inserted_id==1
    else:
      rc=self.db["docs"].update_one({"type_doc":type_doc,"user":user,"id":id_doc},update={"$set":doc})
      return rc.modified_count==1

  def del_doc(self, id_doc, user, type_doc):
    rc=self.db["docs"].delete_one({"id":id_doc,"type_doc":type_doc,"user":user})
    return rc.deleted_count==1

  def add_nft_to_account(self, address, _nft:NFT,occ=1):
    acc=self.get_account(address)
    if not _nft.address in acc.nfts_balances:acc.nfts_balances[_nft.address]=0
    acc.nfts_balances[_nft.address]+=occ
    self.save_account(acc)

  def get_balance(self,addr,token_id=""):
    if len(token_id)==0:
      return 1000
    else:
      acc=self.get_account(addr)
      return acc.nfts_balances[token_id] if token_id in acc.nfts_balances else 0

  def save_account(self, acc:NfluentAccount):
    a=acc.__dict__
    return self.db["accounts"].replace_one(filter={"address":acc.address},replacement=a,upsert=True)

  def save_nft(self, nft):
    _nft=nft.__dict__
    return self.db["nfts"].replace_one(filter={"address":nft.address},replacement=_nft,upsert=True)

  def get_histos(self, addr="",start=0,end=0):
    """
    Retourne l'histo entre deux dates
    :param start:
    :return:
    """
    if end==0:end=now()
    rc=list()
    for t in list(self.db["histo"].find({"addr":addr})):
      if t["ts"]>start and t["ts"]<end: rc.append(t)
    return rc

  def set_account_settings(self, address:str, param:dict):
    self.db["account_settings"].update_one({"address":address},{"$set":param},upsert=True)


  def get_account_settings(self, address:str) -> dict :
    rc=self.db["account_settings"].find_one({"address":address})
    del rc["_id"]
    return rc








