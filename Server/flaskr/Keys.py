import json


class Key(object):
	address:str=""
	secret_key:str=""
	network: str=""
	name:str=""
	seed:str=""

	def __init__(self,secret_key="",name="",address="",network="",seed="",obj=None):
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


	def __str__(self):
		return self.address+" ("+self.name+")"


	def toJson(self):
		return json.dumps(self.__dict__)