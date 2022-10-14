import pymongo
from bson import ObjectId
from pymongo import mongo_client, database

from NFT import NFT
from Tools import log, now
from secret import MONGO_INITDB_ROOT_USERNAME, MONGO_INITDB_ROOT_PASSWORD, MONGO_CLUSTER_CONNECTION_STRING, \
  MONGO_CLUSTER_CONNECTION_STRING_2, WEB3_PASSWORD

#Voir les infos de connections du cloud sur
#Localisation de l'offre cloud :
DB_SERVERS=dict(
  {
    "local":"mongodb://127.0.0.1:27017",
    "server":"mongodb://"+MONGO_INITDB_ROOT_USERNAME+":"+MONGO_INITDB_ROOT_PASSWORD+"@server.f80lab.com:27017",
    "cloud":MONGO_CLUSTER_CONNECTION_STRING,
    "cloud2":MONGO_CLUSTER_CONNECTION_STRING_2,
    "web3":"mongodb://root:"+WEB3_PASSWORD+"@d3akash.cloud:31365/"
  }
)


class DAO:
  db:database=None

  def __init__(self,domain:str="cloud",dbname="nfluent",ope=None):
    if ope:
      self.domain=ope["database"]["connexion"]
      self.dbname=ope["database"]["dbname"]
    else:
      self.dbname=dbname
      self.domain=domain

    log("Initialisation de la base de données "+self.domain+"/"+self.dbname)
    if self.connect(self.domain,self.dbname):
      log("Tentative de connexion ok")


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

    log("Tentative de connexion sur la base de données "+self.dbname+" sur le domain "+DB_SERVERS[self.domain])
    try:
      url=DB_SERVERS[self.domain] if not domain.startswith("mongodb+srv") else self.domain
      self.db: pymongo.mongo_client = pymongo.MongoClient(url)[self.dbname]
      cols=self.db.__dict__
      log("Connexion réussie. ")
      return True

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

  def add_dict(self, data):
    rc=self.db["dicts"].insert_one(data)
    return str(rc.inserted_id)

  def get_dict(self, id):
    return self.db["dicts"].find_one(filter={"_id":ObjectId(id)})

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



  def add_nft_to_mint(self,miner:str,sources:dict,network,collections,dest,dtStart=now()):
    obj={
      "dtCreate":now(),
      "dtStart":dtStart,
      "dtWork":None,
      "network":network,
      "message":"",
      "miner":miner,
      "dest":dest,
      "filter":collections,
      "sources":sources
    }
    log("Ajout dans le mintpool de "+str(obj))
    tx=self.db["mintpool"].insert_one(obj)
    return str(tx.inserted_id)



  def add_validator(self, id,ask_for):
    """
    Ajout d'un nouveau validateur dans la liste
    :param id:
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





