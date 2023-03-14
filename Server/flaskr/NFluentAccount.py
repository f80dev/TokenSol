from flaskr.Keys import Key


class NfluentAccount(Key):
	"""
	Cette classe est la version générique d'un compte sur l'ensemble des blocchain utilisé dans TokenForge
	"""
	balance:int=0
	amount:float=0
	unity:str="egld"
	nonce:int=0
	explorer=""

	def __init__(self,address="",network:str="devnet",balance=0,nonce=0,obj=None,unity="",explorer="",name=""):

		if not obj is None:
			network=obj["network"]
			unity=obj["unity"]
			explorer=obj["explorer"]
			address=obj["address"]
			balance=obj["balance"] if "balance" in obj else obj["solde"]
			nonce=obj["nonce"] if "nonce" in obj else 0

		super().__init__(address=address,network=network,name=name)

		self.balance=balance
		self.amount=float(balance)/1e18
		self.nonce=nonce
		self.unity=unity
		self.explorer=explorer


