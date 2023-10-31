import base64
import json

from flaskr.Tools import encrypt, decrypt


class Key(object):
  address:str=""
  secret_key:str=""
  network: str=""
  name:str=""
  seed:str=""
  balance=0
  explorer=""

  def __init__(self,secret_key="",name="",address="",network="",seed="", encrypted="",explorer="",obj=None):
    assert type(encrypted)==str,"encrypted doit être une chaine de caractères"
    if not encrypted=="":
      obj=dict()
      if ":" in encrypted:encrypted=encrypted.split(":")[1]
      decrypted=decrypt(encrypted.strip())
      if decrypted.startswith("{"):
        obj=json.loads(decrypted)   #Encrypt contient toute la clé
      else:
        obj["secret_key"]=decrypted

    if not obj is None:
      if "name" in obj: name=obj["name"]
      if "secret_key" in obj:
        secret_key=obj["secret_key"]
      else:
        if "private_key" in obj:
          secret_key=obj["private_key"]
        else:
          if "privatekey" in obj:secret_key=obj["privatekey"]
      if "address" in obj:address=obj["address"]
      if "network" in obj:network=obj["network"]
      if "seed" in obj:seed=obj["seed"]

    self.name=name
    self.seed=seed
    self.explorer=explorer
    self.secret_key=secret_key if len(secret_key)<150 else decrypt(base64.b64decode(secret_key))

    if network=="":
      if secret_key.startswith("0x"):network="polygon"
    self.network=network
    self.address=address

  def fromDict(self,obj:dict):
    return self.__init__(obj=obj)

  def encrypt(self,only_private_key=False):
    if not only_private_key:
      return encrypt(self.toJson())
    else:
      return encrypt(self.secret_key)


  def __str__(self):
    if self.address=="" and self.name=="":
      return self.secret_key[:10]+".."
    else:
      return self.address+" ("+self.name+")"


  def toJson(self):
    return json.dumps(self.__dict__)

  def toBytes(self):
    return bytearray.fromhex(self.address)
