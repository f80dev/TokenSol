import os
#from google.cloud import storage
from flaskr.Storage import Storage
from flaskr.Tools import now, get_hash


class GoogleCloudStorageTools(Storage):
  """
  Voir l'authentification
  voir https://console.cloud.google.com/storage/browser/calviontherock
  documentation https://googleapis.dev/python/storage/latest/blobs.html
  """

  def __init__(self):
    os.environ["GOOGLE_APPLICATION_CREDENTIALS"]="calviontherock-a3a222fab18c.json"
#    self.bucket = storage.Client().bucket("calviontherock")
#    self.bucket.make_public()


  def add(self,data:dict,id=None,overwrite=False):
    if id is None: id=data["symbol"]+"_"+str(int(now()))

    blob = self.bucket.blob(id)
    # blob.upload_from_string(dumps(data),content_type="application/json")
    blob.make_public()

    return {"cid":id,"url":blob.public_url,"hash":get_hash(blob)}



