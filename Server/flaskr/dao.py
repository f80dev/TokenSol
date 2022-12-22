import hashlib
import pymongo
from bson import ObjectId
from pymongo import mongo_client, database

from flaskr.NFT import NFT
from flaskr.Tools import log, now
from flaskr.secret import MONGO_INITDB_ROOT_USERNAME, MONGO_INITDB_ROOT_PASSWORD, MONGO_CLUSTER_CONNECTION_STRING, MONGO_WEB3_CONNECTION_STRING

#Voir les infos de connections du cloud sur
#Localisation de l'offre cloud :
DB_SERVERS=dict(
  {
    "local":"mongodb://127.0.0.1:27017",
    "server":"mongodb://"+MONGO_INITDB_ROOT_USERNAME+":"+MONGO_INITDB_ROOT_PASSWORD+"@server.f80lab.com:27017",
    "cloud":MONGO_CLUSTER_CONNECTION_STRING,
    "web3":MONGO_WEB3_CONNECTION_STRING
  }
)


class DAO:
  db:database=None
  url:str=""

  def __init__(self,domain:str="web3",dbname="nfluent",ope=None,config=None,network=""):
    if ope:
      self.domain=ope["database"]["connexion"]
      self.dbname=ope["database"]["dbname"]
    else:
      if config:
        if config["DB_SERVER"] in DB_SERVERS:config["DB_SERVER"]=DB_SERVERS[config["DB_SERVER"]]
        self.dbname=config["DB_NAME"]
        self.domain=config["DB_SERVER"]
      else:
        if len(network)>0:
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
    #log("Tentative de connexion sur la base de données "+self.dbname+" sur "+self.url)
    try:
      self.db: pymongo.mongo_client = pymongo.MongoClient(self.url)[self.dbname]
      return self.db.list_collections().alive
    except Exception as inst:
      log("Base de données non disponible "+str(inst.args))
      self.db=None

    return False



  def lazy_mint(self, nft,ope,server_addr="https://server.f80lab.com",id=""):
    """
    Opere un transfert du NFT dans la base de données
    :param _data:
    :param ope:
    :param server_addr:
    :param id:
    :return:
    """
    _data=nft.__dict__
    _data["address"]="db_"+now("hex")[2:]     #l'addresse commençant par db_ permet de désigner une base de données
    _data["ts"]=int(now()*1000)
    _data["ope"]=ope

    result=self.db["nfts"].replace_one(filter={"address":_data["address"]},replacement=_data,upsert=True)
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


  def get(self, id):
    rc=self.db["nfts"].find_one(filter={"id":id})
    if not rc is None:del rc["_id"]
    return rc

  def delete(self, id):
    return self.db["nfts"].delete_one(filter={"id":id})

  def add_data(self, data):
    if type(data)==str:data={"content":data}
    rc=self.db["storage"].insert_one(data)
    return str(rc.inserted_id)

  def get_data(self, id):
    return self.db["storage"].find_one(filter={"_id":ObjectId(id)})

  def add_histo(self, ope,command,account, collection_id,transaction_id,network="",comment="",params=list()):
    if not self.db is None:
      self.db["histo"].insert_one({
        "operation":ope,
        "command":command,
        "addr":account,
        "collection":collection_id,
        "ts":now(),
        "transaction":transaction_id,
        "network":network,
        "comment":comment,
        "params":params
      })



  def update(self, _data,field="quantity"):
    """
    Mise a jour de la quantité
    :param _data:
    :param field:
    :return:
    """
    self.db["nfts"].update_one({"address":_data["address"]},{ "$set": { field: _data[field] } })


  def get_mintpool(self):
    return list(self.db["mintpool"].find())

  def reset_mintpool(self):
    try:
      self.db["mintpool"].drop()
    except:
      pass

  def get_nfts_to_mint(self,limit=100,filter_id=""):
    """
    retourne la file d'attente de minage
    :param limit:
    :return:
    """
    asks=[]
    for transaction in self.db["mintpool"].find({"dtWork":None}):
      if transaction["dtStart"]<now() and (len(filter_id)==0 or str(transaction["_id"])==filter_id):
        asks.append(transaction)

    return asks[:limit]



  def edit_pool(self,id,dtWork,message):
    """
    Confirme la réalisation d'un travail
    :param id:
    :param dtWork:
    :return:
    """
    rc=self.db["mintpool"].update_one({"_id":id},{"$set":{"dtWork":dtWork,"message":message}})
    return rc.modified_count



  def add_nft_to_mint(self,miner:str,sources:dict,network,collections,destinataires,wallet,operation,dtStart=now(),collection_to_mint=None):
    if type(destinataires)==str:destinataires=[destinataires]

    for d in destinataires:
      if len(d)>3:
        obj={
          "dtCreate":now(),
          "dtStart":dtStart,
          "dtWork":None,
          "operation":operation,
          "network":network,
          "message":"",
          "miner":miner,
          "dest":d,
          "filter":collections,
          "collection_to_mint":collection_to_mint,
          "sources":sources,
          "wallet":wallet
        }
        log("Ajout dans le mintpool de "+str(obj))
        tx=self.db["mintpool"].insert_one(obj)

    return str(tx.inserted_id)

  def add_email(self,email:str,addr:str,network:str):
    encoded_email=hashlib.sha256(email.encode()).hexdigest()
    self.db["account_by_emails"].insert_one({
      "email":encoded_email,
      "address":addr,
      "network":network
    })

  def get_address(self,email:str,network:str):
    encoded_email=hashlib.sha256(email.encode()).hexdigest()
    rc=self.db["account_by_emails"].find_one({"email":encoded_email,"network":network})
    if rc:return rc["address"]
    return rc



  def add_validator(self, id,ask_for):
    """
    Ajout d'un nouveau validateur dans la liste
    :param ask_for contient une collection ou une liste de NFT
    :return:
    """
    self.db["validators"].update_one({"id":id},{"$set":{
      "id":id,
      "dtStart":now(),
      "ask":ask_for,
      "user":"",
      "nfts":0
    }
    },upsert=True)



  def get_nft(self, nft_addr):
    return NFT(object=self.db["nfts"].find_one({"address":nft_addr}))




