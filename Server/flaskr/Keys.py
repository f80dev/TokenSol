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

	def __init__(self,secret_key="",name="",address="",network="",seed="",obj=None, encrypted=""):
		if len(encrypted)>0:
			decrypted=decrypt(encrypted)
			if decrypted.startswith("{"): obj=json.loads(decrypted)

		if not obj is None:
			if "name" in obj: name=obj["name"]
			if "secret_key" in obj:secret_key=obj["secret_key"]
			if "address" in obj:address=obj["address"]
			if "network" in obj:network=obj["network"]
			if "seed" in obj:seed=obj["seed"]

		self.name=name
		self.seed=seed
		self.secret_key=secret_key
		if network=="":
			if secret_key.startswith("0x"):network="polygon"
		self.network=network
		self.address=address


	def encrypt(self):
		return encrypt(self.toJson())


	def __str__(self):
		return self.address+" ("+self.name+")"


	def toJson(self):
		return json.dumps(self.__dict__)