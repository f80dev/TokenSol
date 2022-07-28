import os
from json import dumps, JSONEncoder, dump

from Tools import now
#from google.cloud import storage

class GoogleCloudStorageTools:
  """
  Voir l'authentification
  voir https://console.cloud.google.com/storage/browser/calviontherock
  documentation https://googleapis.dev/python/storage/latest/blobs.html
  """

  def __init__(self):
    os.environ["GOOGLE_APPLICATION_CREDENTIALS"]="calviontherock-a3a222fab18c.json"
#    self.bucket = storage.Client().bucket("calviontherock")
#    self.bucket.make_public()


  # def add(self,data:dict,id=None):
  #   if id is None: id=data["symbol"]+"_"+str(int(now()))
  #
  #   blob = self.bucket.blob(id)
  #   blob.upload_from_string(dumps(data),content_type="application/json")
  #   blob.make_public()
  #
  #   return {"cid":id,"url":blob.public_url}



