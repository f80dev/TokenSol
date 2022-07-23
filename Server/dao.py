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

    log("Ouverture de la base de données "+self.dbname+" sur le domain "+DB_SERVERS[self.domain])
    try:
      url=DB_SERVERS[self.domain] if not domain.startswith("mongodb+srv") else self.domain
      self.db: pymongo.mongo_client = pymongo.MongoClient(url)[self.dbname]
    except Exception as inst:
      log("Base de données non disponible "+str(inst.args))
      self.db=None


  def lazy_mint(self, _data,ope,server_addr="https://server.f80lab.com",id=""):
    """
    Opere un transfert du NFT dans la base de données
    :param _data:
    :param ope:
    :param server_addr:
    :param id:
    :return:
    """
    if "_id" in _data:del _data["_id"]
    if not "id" in _data:
      if len(id)==0: id=_data["collection"]["name"]+"_"+_data["symbol"]
      _data["id"]=id

    _data["ts"]=int(now()*1000)
    _data["ope"]=ope
    _data["quantity"]=_data["marketplace"]["max_mint"]
    result=self.db["nfts"].replace_one(filter={"id":_data["id"]},replacement=_data,upsert=True)
    rc={
      "error":"",
      "result":{"transaction":_data["id"],"mint":_data["id"]},
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
      nfts=self.db["nfts"].find(filter={"collection.name":col["name"]})
    else:
      nfts=self.db["nfts"].find()

    for nft in nfts:
      _nft=NFT(object=nft)
      if "max_mint" in nft.marketplace :_nft.marketplace["quantity"]=nft.marketplace["max_mint"]
      rc.append(_nft.__dict__)

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
    self.db["nfts"].update_one({"id":_data["id"]},{ "$set": { field: _data[field] } })



