from bson import ObjectId
from flaskr import DAO
from flaskr.Keys import Key
from flaskr.Tools import now, log, get_operation, random_from, is_email, send
from flaskr.apptools import get_nfts_from_src, get_network_instance, transfer


class Mintpool:
	config=None
	
	def __init__(self,config=None):
		self.config=config
		self.pool=DAO(config=config).db["mintpool"]

	def get_mintpool(self):
		return list(self.pool.find())


	def add_ask(self,sources:[dict],target:dict,wallet,operation,dtStart=now()):
		"""
		Ajouter une tache dans la pool de mining
		:param sources: doit contenir le network et le mineur a utiliser
		:param target: doit contenir le mineur de la cible, le nom du réseau et eventuellement la collection à utiliser
		:param destinataires:
		:param wallet:
		:param operation:
		:param dtStart:
		:param collection_to_mint:
		:return:
		"""

		for src in sources:
			if not "miner" in src or not "network" in src: raise RuntimeError("Sources incomplete")
		if not "miner" in target or not "network" in target: raise RuntimeError("Target incomplete")

		obj={
			"dtCreate":now(),
			"dtStart":dtStart,
			"dtWork":None,
			"operation":operation,
			"target":target,
			"message":"",
			"sources":sources,
			"wallet":wallet
		}
		log("Ajout dans le mintpool de "+str(obj))
		tx=self.pool.insert_one(obj)

		return str(tx.inserted_id)


	def reset_mintpool(self):
		"""
		efface la file d'attente de minage
		:return:
		"""
		try:
			self.pool.drop()
		except:
			pass




	def get_nfts_to_mint(self,limit=100,filter_id=""):
		"""
		retourne la file d'attente de minage
		:param limit:
		:return:
		"""
		asks=[]
		for transaction in self.pool.find({"dtWork":None}):
			if transaction["dtStart"]<now() and (len(filter_id)==0 or str(transaction["_id"])==filter_id):
				asks.append(transaction)

		return asks[:limit]



	def edit_pool(self,id,dtWork,message):
		"""
		Confirme la réalisation d'un travail
		:param id:
		:param dtWork:
		:return:
		"""
		rc=self.pool.update_one({"_id":id},{"$set":{"dtWork":dtWork,"message":message}})
		return rc.modified_count>0

	
	def delete(self, id):
		rc=self.pool.delete_one({"_id":ObjectId(id)})
		return rc.deleted_count==1

	@staticmethod
	def create_target(miner:Key,network:str,owner:str="",collection:str=""):
		"""
		Permet de fabriquer des sources utile pour async_mint
		:param miner:
		:param network:
		:param owner:
		:param collection: utlisé pour miner
		:return:
		"""
		if owner=="": owner=miner.address
		if "elrond" in network and collection=="": raise RuntimeError("Pour Elrond vous devez préciser une collection")
		rc={
			"active":True,
			"miner":miner.__dict__,
			"network":network,
			"collection":collection,
			"owner":owner
		}
		return rc

	@staticmethod
	def create_source(miner:Key,network:str,owner:str="",collection:str=""):
		"""
		Permet de fabriquer des sources utile pour async_mint
		:param miner:
		:param network:
		:param owner:
		:param collection:
		:return:
		"""
		rc={
			"active":True,
			"miner":miner.__dict__,
			"network":network,
		}
		if len(owner)>0:rc["owner"]=owner
		if len(collection):rc["collection"]=collection
		return rc


	def async_mint(self,nbr_items=3,filter="") -> int:
		n_treatment=0
		message=""

		# if not dao.isConnected():
		#   message="Impossible de se connecter à la base"
		#   return n_treatment
		
		if message=="":
			for ask in self.get_nfts_to_mint(int(nbr_items),filter):
				log("Traitement de la demande "+str(ask["_id"]))
				if self.edit_pool(ask["_id"],now(),"traitement en cours"):
					src=random_from(ask["sources"])
					nfts=get_nfts_from_src([src],False)
					_ope=get_operation(ask["operation"])
		
					nft_to_mint=None
					_target_network=get_network_instance(ask["target"]["network"])
					_target_miner:Key=Key(obj=ask["target"]["miner"])
					_from_miner:Key=Key(obj=src["miner"])
		
					if len(nfts)>0:
						log("Tirage au sort d'un NFT parmis la liste de "+str(len(nfts)))
		
						nft_to_mint=random_from(nfts)
		
						# if nft_to_mint.owner=="":
						#   if nft_to_mint.collection is None:
						#     nft_to_mint.collection=_network.get_collection(ask["collection_to_mint"])
						#
						#   if _network.canMint(nft_to_mint,ask["dest"]): break
						# else:
						#   if not _miner is None and nft_to_mint.owner==_miner.address: break
					else:
						log("Aucun NFT à miner depuis la source "+str(ask["sources"]))
						self.edit_pool(ask["_id"],now(),"Aucun NFT dans la source "+str(ask["sources"]))
		
		
		
					# Démarage du minage
					if not nft_to_mint is None:
						log("Minage de "+nft_to_mint.name+" en cours")
						# if _miner is None:
						#   log("Le miner est fixé sur le propriétaire de la collection "+nft_to_mint.collection["id"])
						#   if "elrond" in ask["network"]:
						#     _miner=elrond.toAccount(nft_to_mint.collection["owner"])
						#     if _miner.secret_key is None:
						#       message="On ne dispose pas de la clé privée du propriétaire de la collection "+nft_to_mint.collection["id"]+", donc pas de minage possible"
						#       #activity_report_sender(message)
		
						if message=="":
							log("Ajout de l'attribut lazymint pour ne pas risquer de re-minté")
							nft_to_mint.attributes.append({"trait_type":"lazymint","value":nft_to_mint.address})
							dest=ask["target"]["owner"]
							if is_email(dest):
								dest=_target_network.create_account( dest,
								                              mail_new_wallet=_ope["new_account"]["mail"] if not _ope is None else "",
								                              mail_existing_wallet=_ope["transfer"]["mail"] if not _ope is None else ""
								                              )
							rc=transfer(addr=nft_to_mint.address,
							            from_network_miner=_from_miner,
							            target_network_miner=_target_miner,
							            from_network=src["network"],
							            target_network=ask["target"]["network"],
							            target_network_owner=dest,collection=ask["target"]["collection"])

							if not rc or rc["error"]!="":
								log("Problème de minage voir "+rc["hash"])
								message="Error"+rc["error"]+" voir "+_target_network.getExplorer(rc["hash"])
							else:
								message="Ok voir "+_target_network.getExplorer(rc["result"]["mint"])
								n_treatment=n_treatment+1
		
						log("Mise a jour des données de la pool de minage avec message:"+message)
						if self.edit_pool(ask["_id"],now(),message): send(self.config,"mintpool_refresh",{"id":ask["_id"]})
				else:
					message="Aucun NFT disponible pour le minage"
					log(message)
					if self.edit_pool(ask["_id"],now(),message): send(self.config,"mintpool_refresh",{"id":ask["_id"]})

		return n_treatment

