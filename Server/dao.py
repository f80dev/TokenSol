import pymongo
from bson import ObjectId
from pymongo import mongo_client

from Tools import log, now
from secret import MONGO_INITDB_ROOT_USERNAME, MONGO_INITDB_ROOT_PASSWORD, MONGO_CLUSTER_CONNECTION_STRING


#Voir les infos de connections du cloud sur
DB_SERVERS=dict(
  {
    "local":"mongodb://127.0.0.1:27017",
    "server":"mongodb://"+MONGO_INITDB_ROOT_USERNAME+":"+MONGO_INITDB_ROOT_PASSWORD+"@server.f80lab.com:27017",
    "cloud":MONGO_CLUSTER_CONNECTION_STRING
  }
)


class DAO:
  db:mongo_client=None

  def __init__(self,domain:str="cloud",dbname="dealer_machine"):
    log("Ouverture de la base de données "+dbname+" sur le domain "+DB_SERVERS[domain])
    try:
      url=DB_SERVERS[domain]
      self.db: pymongo.mongo_client = pymongo.MongoClient(url)[dbname]
    except Exception as inst:
      log("Base de données non disponible "+str(inst.args))
      self.db=None

  def mint(self, _data,ope,server_addr="https://server.f80lab.com",id=""):
    if len(id)==0: id=_data["collection"]["name"]+"_"+_data["symbol"]
    if "_id" in _data:del _data["_id"]
    _data["id"]=id
    _data["uri"]=server_addr+"/api/nfts/"+id
    _data["ts"]=int(now()*1000)
    _data["ope"]=ope
    result=self.db["nfts"].replace_one(filter={"id":id},replacement=_data,upsert=True)
    rc={
      "error":"",
      "result":{"transaction":"","mint":id},
      "balance":0,
      "link_mint":"",
      "uri":_data["uri"],
      "link_transaction":"",
      "out":"",
      "command":"insert"
    }
    return rc

  def nfts_from_collection(self, col):
    return self.db["nfts"].find(filter={"collection.name":col})

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

  def add_histo(self, account, collection_id):
	  self.db["histo"].insert_one({"addr":account,"collection":collection_id,"ts":now()})

