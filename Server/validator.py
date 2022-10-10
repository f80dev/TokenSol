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
    self.dao.add_validator(id)



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
    """
    On récupére l'ensemble des NFT en local
    :return:
    """
    if self.init_operation():
      self.nfts=[]
      elrond=Elrond(self.operation["network"])
      for nft in elrond.get_nfts_from_collections(self.operation["validate"]["filters"]["collections"]):
        if nft.owner=="": nft=elrond.get_nft(nft.address)

        self.nfts.append(nft)

    #On informe de la dernière connexion et du nombre de nft possédé
    self.dao.db["validators"].update_one({"id":self.id},{"$set":{"dtLastConnexion":now(),"nfts":len(self.nfts)}})



  def success(self):
    print("Validation ok")



  def run(self):
    """
    Cette fonction vérifie que le user_to_validate possède bien les NFT requis par l'opération
    :return:
    """
    if self.init_operation():
      user_to_validate=self.dao.db["validators"].find_one({"id":self.id})["user"]
      if len(user_to_validate)>0:
        if user_to_validate in [x.owner for x in self.nfts]:
          self.dao.db["validators"].update_one({"id":self.id},{"$set":{"user":""}})
          self.success()
          return True

      return True
    else:
      return False



scheduler = BackgroundScheduler()
@atexit.register
def destroy():
  if scheduler.running:
    scheduler.shutdown()



if __name__ == '__main__':
  validator=Validator(argv[1])
  validator.get_nfts()

  scheduler.add_job(func=validator.get_nfts, trigger="interval", seconds=20)      #Récupération de l'ensemble des NFT à fréquence régulière
  scheduler.add_job(func=validator.run, trigger="interval", seconds=2)
  scheduler.start()

  while True:
    time.sleep(20)
