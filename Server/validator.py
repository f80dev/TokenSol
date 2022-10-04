import atexit
from sys import argv
import time

from apscheduler.schedulers.background import BackgroundScheduler

from Elrond.Elrond import Elrond
from Tools import now, get_operation
from dao import DAO

class Validator:

  dao=DAO()
  operation={}
  nfts=[]

  def __init__(self,id=""):
    self.id=id if len(id)>0 else "validator_"+now("hex")
    self.dao.db["validators"].update_one({"id":self.id},{"$set":{
      "id":self.id,
      "dtStart":now(),
      "operation":"",
      "user":"",
      "nfts":0
    }
    },upsert=True)


  def init_operation(self):
    if self.operation=={}:
      try:
        yaml_location=self.dao.db["validators"].find_one({"id":self.id})["operation"]
        if len(yaml_location)==0:return False
        self.operation=get_operation(yaml_location)
        return True
      except:
        return False
    else:
      return True


  def get_nfts(self):
    if self.init_operation():
      self.nfts=Elrond(self.operation["network"]).get_nfts_from_collections(self.operation["validate"]["filters"]["collections"])
      self.dao.db["validators"].update_one({"id":self.id},{"$set":{"dtLastConnexion":now(),"nfts":len(self.nfts)}})


  def success(self):
    print("Validation ok")



  def run(self):
    if self.init_operation():
      user_to_validate=self.dao.db["validators"].find_one({"id":self.id})["user"]
      if len(user_to_validate)>0:
        for nft in self.nfts:
          if nft["owner"]==user_to_validate:
            self.dao.db["validators"].update_one({"id":self.id},{"$set":{"user":""}})
            self.success()


scheduler = BackgroundScheduler()
@atexit.register
def destroy():
  if scheduler.running:
    scheduler.shutdown()



if __name__ == '__main__':
  validator=Validator(argv[1])
  nfts=Elrond("elrond-devnet").get_nfts_from_collections(["BAYARD-2018c7"])

  scheduler.add_job(func=validator.get_nfts, trigger="interval", seconds=20)
  scheduler.add_job(func=validator.run, trigger="interval", seconds=2)
  scheduler.start()

  while True:
    time.sleep(20)
