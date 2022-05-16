import pymongo
from pymongo import mongo_client

from Tools import log
from secret import MONGO_INITDB_ROOT_USERNAME, MONGO_INITDB_ROOT_PASSWORD

DB_SERVERS=dict(
  {
    "local":"mongodb://127.0.0.1:27017",
    "server":"mongodb://"+MONGO_INITDB_ROOT_USERNAME+":"+MONGO_INITDB_ROOT_PASSWORD+"@server.f80lab.com:27017",
    "cloud":"mongodb+srv://"+MONGO_INITDB_ROOT_USERNAME+":"+MONGO_INITDB_ROOT_PASSWORD+"@kerberus-44xyy.gcp.mongodb.net/test"
  }
)


class DAO:
  db:mongo_client=None

  def __init__(self,domain:str="cloud",dbname="dealer_machine"):
    log("Ouverture de la base de données "+dbname)
    try:
      log("Connexion à la base de donnée "+DB_SERVERS[domain])
      url=DB_SERVERS[domain]
      self.db: pymongo.mongo_client = pymongo.MongoClient(url)[dbname]
    except Exception as inst:
      log("Base de données non disponible "+str(inst.args))
      self.db=None

  def mint(self, _data):
    id=_data["symbol"]+_data["collection"]["name"]
    _data["id"]=id
    result=self.db["nfts"].replace_one(filter={"id":id},replacement=_data,upsert=True)
    rc={
      "error":"",
      "result":{
        "transaction":"",
        "mint":id
      },
      "balance":0,
      "link_mint":"",
      "link_transaction":"",
      "out":"",
      "command":"insert"
    }
    return rc

  def nfts_from_collection(self, col):
    return self.db["nfts"].find(filter={"collection.name":col})

  def get(self, id):
    rc=self.db["nfts"].find_one(filter={"id":id})
    del rc["_id"]
    return rc

  def delete(self, id):
    return self.db["nfts"].delete_one(filter={"id":id})

