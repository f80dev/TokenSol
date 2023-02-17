import base64
from json import loads

from flaskr.Mintpool import Mintpool
from flaskr.Network import Network
from flaskr.Tools import get_operation, now, get_key_by_name
from flaskr.settings import OPERATIONS_DIR
from tests.test_art import test_generate_collection
from tests.test_tools import *

@pytest.fixture()
def operation():
	return get_operation("Main_devnet")



def get_account_from_network(test_client, network=MAIN_NETWORK, seuil=1, filter="bob,carol,dan,eve,frank,grace",all=False) -> dict:
	"""Retourne un compte avec au moins x egld"""
	log("Récuperation des comptes de "+network)
	accounts = call_api(test_client, "accounts/", "?network=" + network)
	rc=[]
	for k in accounts:
		if k["amount"]>=seuil and (len(filter) == 0 or k["name"] in filter):
			rc.append(k)

	if all: return rc

	if len(rc)==0:
		log("Pas de compte disponible disposant d'un solde supérieur au solde")
		return None
	else:
		return random_from(rc)


def test_get_account_for_all_network(test_client):
	log("Récupération des comptes des l'ensemble des networks")
	for n in NETWORKS:
		accounts=get_account_from_network(test_client,n,0,all=True)
		assert not accounts is None


def test_accounts(test_client, network=MAIN_NETWORK, seuil=1,filter="bob,carol,dan,eve,frank,grace"):
	log("Récupération des comptes du network "+network+" avec seuil a "+str(seuil))
	rc = get_account_from_network(test_client, network, 0,filter=filter)
	assert rc is not None, "Aucun compte disponible"

	rc = get_account_from_network(test_client, network, seuil=seuil,filter=filter)
	assert rc != None, "Aucun compte disponible avec un solde > " + str(seuil)
	assert rc["amount"] >= seuil

	rc = get_account_from_network(test_client, network, seuil=1000000000,filter=filter)
	assert rc is None, "Le solde ne doit pas fonctionner"



def test_getyaml(test_client):
	rc = call_api(test_client, "getyaml/Main_devnet/", "dir="+OPERATIONS_DIR)
	assert rc["id"] == "Main_devnet"



def test_faqs(test_client):
	rc=call_api(test_client,"getyaml/faqs/","dir=./flaskr/static")
	for faq in rc["content"]:
		print("Analyse de "+faq["index"])
		assert "index" in faq,"index manquant"
		assert "content" in faq,"content manquant"
		assert "title" in faq,"title manquant"


def test_api_upload_json(test_client,objs=["bonjour comment allez vous",{"key":"value"}],platforms=PLATFORMS):
	"""
	test d'un upload de json sur l'ensemble des platformes
	:param test_client:
	:param objs:
	:param platforms:
	:return:
	"""
	for p in platforms:
		for obj in objs:
			log("Test de la platform "+p)
			cid=call_api(test_client,"upload/","platform="+p,obj)
			assert len(cid["url"])>0
			assert len(cid["cid"])>0


def test_api_upload(test_client,files=["batch_importation.xlsx","CV.docx","doc.pdf","fond1.gif","image_1.webp"],platforms=PLATFORMS):
	for p in platforms:
		log("Test de la platform "+p)
		for f in files:
			with open(RESSOURCE_TEST_DIR+f,"rb") as file: bytes=file.read()
			_type="application/"+f.split(".")[1]

			if "image" in _type or p!="nftstorage":
				body={
					"filename":f,
					"content":"data:"+_type+";base64,"+str(base64.b64encode(bytes),"utf8"),
					"type":_type
				}
				cid=call_api(test_client,"upload/","platform="+p,body)
				assert len(cid["url"])>0
				assert len(cid["cid"])>0

				if not "ipfs" in p:
					log("Tentative de récupération du fichier "+cid["url"])
					resp=test_client.get(cid["url"])
					assert resp.status_code==200 or p=="infura"


def test_seach_images(test_client,query="lapin"):
	rc=call_api(test_client,"search_images/","query="+query+"&remove_background=true")
	assert len(rc)>0




def test_api_upload_batch(test_client, file=RESSOURCE_TEST_DIR+"batch_importation.xlsx", miner=MAIN_ACCOUNT):
	rc = call_api(test_client, "upload_batch/", body={"content": file})
	assert not rc is None


def test_api_get_collections(test_client, network=MAIN_NETWORK, col_or_account=MAIN_COLLECTION):
	rc = call_api(test_client, "collections/" + col_or_account + "/", "network=" + network + "&with_detail=true&limit=100")
	assert not rc is None
	return rc




def test_infos(test_client):
	rc = call_api(test_client, "infos/")
	assert "Server" in rc
	assert "Client" in rc
	assert "Static_Folder" in rc
	assert "Upload_Folder" in rc



def test_keys_networks(test_client,networks=NETWORKS):
	for network in networks:
		if not Network(network).is_blockchain():
			get_network_instance(network).create_account("paul.dudule@gmail.com")
			get_network_instance(network).create_account("sophie.dudule@gmail.com",10)

		print("Analyse du réseau "+network)
		#test_keys(test_client,network,0,"")




def test_create_account_from_email(network=MAIN_NETWORK,email=MAIN_EMAIL,send_real_email=True):
	_net=get_network_instance(network)
	rc=_net.create_account(email=email,send_real_email=send_real_email)
	assert not rc is None
	assert len(rc.address)>0
	assert len(rc.secret_key)>0
	return rc


def test_nfts_from_collection(test_client, col_id="", network=MAIN_NETWORK):
	if col_id == "":
		cols = test_api_get_collections(test_client, network)
		col_id = cols[0]["id"]

	rc = call_api(test_client, "nfts_from_collection/" + col_id + "/", "network=" + network)
	assert not rc is None
	return rc["nfts"]


def test_nfts_from_owner(test_client, owner=MAIN_ACCOUNT, network=MAIN_NETWORK,seuil=1):
	"""
  Récupére les nfts d'une collection ou d'un client
  :param test_client:
  :return:
  """
	if owner == "":
		account = get_account_from_network(test_client, network=network, seuil=1)
		owner = account["address"]

	rc = call_api(test_client, "nfts/", "account=" + owner + "&network=" + network)
	assert len(rc) >= seuil

	return rc


def test_find_collection_for_networks(test_client,networks=NETWORKS):
	for network in networks:
		miner=MAIN_ACCOUNTS[network.split("-")[0]]
		cols = call_api(test_client, "collections/" + miner + "/", "filter_type=NonFungibleESDT&network="+network)
		assert not cols is None

def find_collection_to_mint(test_client, miner:str,network="elrond-devnet"):
	cols = call_api(test_client, "collections/" + miner + "/", "filter_type=NonFungibleESDT&network="+network)
	if len(cols) > 0:
		col_id = None
		for col in cols:
			if not col_id:
				for role in col["roles"]:
					if role["canCreate"] and miner == role["address"]:
						col_id = col["collection"]
						return col_id
	return None


def mint_from_file(test_client, filename: str = RESSOURCE_TEST_DIR+"image_1.webp", miner=MAIN_ACCOUNT,
                        network=MAIN_NETWORK, col_id=MAIN_COLLECTION):
	with open(filename.replace(".webp", ".xmp")) as file: s = file.read()
	_data = loads(str(base64.b64decode(s.split("mint='")[1].split("'")[0]), "utf8"))
	_data["collection"] = {"id": col_id}
	nft = NFT(object=_data)
	rc=None
	#rc = mint(nft, miner, miner, network)
	assert not rc is None
	assert len(rc["error"]) == 0, "Erreur " + rc["error"] + " hash=" + rc["hash"]
	return rc


def test_mint_polygon(test_client,network="polygon-devnet"):
	miner=random_from(get_network_instance(network).get_keys())
	test_api_mint(test_client,miner=miner,col_id="",network=network)



def test_mint_file(test_client,network="file-testnet"):
	miner=random_from(get_network_instance(network).get_keys())
	token_id,col_id=test_api_mint(test_client,miner=miner,col_id="MACOLLEC",network=network)
	assert not token_id is None
	nft=get_network_instance(network).get_nft(token_id)
	assert not nft is None
	assert nft.address==token_id

def test_api_mint(test_client, miner:Key=None, col_id=MAIN_COLLECTION, network=MAIN_NETWORK,platform=MAIN_STORAGE_PLATFORM) -> (str, str):
	if miner is None:
		miner=random_from(get_network_instance(network).get_keys())
		cols = test_api_get_collections(test_client, network,miner.address)
		col_id=random_from(cols)["id"]
		if len(cols)==0:
			col=test_create_collection(test_client,"LaCollec",miner,network)
			col_id=col["id"]

	if col_id == "":
		col_id = find_collection_to_mint(test_client, miner.address,network)

	_account=test_get_account(test_client,miner.address,network)
	assert _account.amount>0.1,"Solde insuffisant pour miner sur le compte "+miner.address               # 0.1 est le prix moyen

	if col_id:
		_nft = create_nft("test_" + now("hex"), col_id)
		rc = call_api(test_client, "mint/",
		              params="network="+network+"&offchaindata_platform="+platform,
		              body={"nft":_nft.__dict__,"miner":miner.__dict__},
		              method="POST")
		assert not rc is None
		assert len(rc["error"]) == 0, rc["error"]
		assert "mint" in rc["result"]

		token_id = rc["result"]["mint"]
		return token_id, col_id


def test_lazymint(test_client, network=DB_NETWORK, collection_to_use=MAIN_COLLECTION,miner=None) -> (str, str):
	"""
  Execute un minage vers la base de données
  :param test_client:
  :param network:
  :return:
  """
	if miner is None:miner=random_from(get_network_instance(network).get_keys())
	log("Test de creation d'un NFT de la collection " + collection_to_use + " dans " + DB_NETWORK)
	assert "db-" in network, "fonction uniquement valable pour miner dans une base de données"
	nft_id, col_id = test_api_mint(test_client, miner=miner,col_id=collection_to_use,network=network)
	assert not nft_id is None
	assert network in nft_id.split("/")[1]
	assert not col_id is None

	#récupération du NFT
	nft=DAO(network).get_nft(nft_id)
	assert not nft is None
	assert nft.marketplace["quantity"]>0
	assert nft.miner==miner.address
	assert nft.owner==miner.address

	return nft_id, col_id


def test_transfer_all_networks(test_client, networks=NETWORKS):
	for from_network in networks:
		for to_network in networks:
			log("Test du transfer de "+from_network+" vers "+to_network)
			miner_for_target_network=get_main_account_for_network(to_network)
			rc=test_transfer_to(test_client,from_network,to_network,miner_for_target_network)

			assert rc, "Le transfert n'a pas eu lieu"


def test_registration_and_login(test_client,email=MAIN_EMAIL,with_delete=True):
	rc=call_api(test_client,"registration/"+email+"/")
	assert "email" in rc
	assert "alias" in rc
	assert len(rc["perms"])>0
	assert "access_code" in rc

	account=call_api(test_client,"login/"+email+"/"+rc["access_code"]+"/?with_api=False")
	assert "email" in account
	assert account["email"]==encrypt(email,short_code=40)

	if with_delete:
		rc=call_api(test_client,"/delete_user/"+email+"/"+rc["access_code"]+"/",method="DELETE")
		return rc
	else:
		return account



def test_update_access_code(test_client,email=MAIN_EMAIL,new_password="",with_delete=True):
	if len(new_password)==0:new_password=now("hex")[2:].upper()
	user=test_registration_and_login(test_client,email,False)
	rc=call_api(test_client,"change_password/"+email+"/"+user["access_code"]+"/"+new_password+"/")
	assert len(rc["error"])==0
	account=call_api(test_client,"login/"+email+"/"+new_password+"/?with_api=False")
	assert not account is None
	if with_delete: call_api(test_client,"/delete_user/"+email+"/"+new_password+"/",method="DELETE")



def test_add_key(test_client,email=MAIN_EMAIL,network=MAIN_NETWORK,name="lucette"):
	user=test_registration_and_login(test_client,email,False)
	keys=call_api(test_client,"keys/")

	obj={
		"network":network,
		"email":email,
		"secret_key":keys[0]["secret_key"],
		"access_code":user["access_code"]
	}
	rc=call_api(test_client,"keys/"+name+"/","",obj)

	rc=call_api(test_client,"keys/","network="+network+"&access_code="+user["access_code"])

	user=test_registration_and_login(test_client,email,False)
	assert "email" in user
	assert len(user["keys"])==1





def test_transfer_to(test_client, from_network=MAIN_NETWORK, to_network=MAIN_NETWORK, miner_for_target_network:Key=None, token_id="", dest:Key=None):
	_from_network=get_network_instance(from_network)
	_to_network=get_network_instance(to_network)

	if token_id == "":
		owner:Key=random_from(_from_network.get_keys())
		nfts=test_nfts_from_owner(test_client,owner.address,from_network,0)
		if len(nfts)>0:
			token_id=random_from(nfts)["address"]
		else:
			token_id, col_id = test_api_mint(test_client, miner=owner, network=from_network)

	if miner_for_target_network is None:
		miner_for_target_network=random_from(_from_network.get_keys())

	if dest is None:
		dest=random_from(_to_network.get_keys())

	if dest is None:
		dest=_to_network.create_account("sophie.dudule@gmail.com")  #On ajoute un compte
		# _to_network.add_key(dest,"sophie")
		# _to_network.faucet(dest.address,0.05,"bank")

	# while len(dest)==0 or dest==miner_for_target_network:
	# 	account = get_account_from_network(test_client, network=to_network, seuil=0,filter="")
	# 	dest = account["address"]

	body={"token_id":token_id,"dest":dest.address,"miner":miner_for_target_network.__dict__}
	rc = call_api(test_client, "transfer/","from_network=" + from_network + "&to_network=" + to_network,body, method="POST")

	assert not rc is None
	assert len(rc["error"]) == 0
	assert len(rc["token_id"]) > 0
	nfts = call_api(test_client, "nfts/", "account=" + dest.address + "&network=" + to_network + "&limit=2000")
	assert rc["token_id"] in [nft["address"] for nft in nfts], "Le NFT n'est pas présent dans le wallet du destinataire"

	return True


def test_raz_validators(test_client):
	log("Effacement des validateurs")
	vals = call_api(test_client, "validators/")
	for val in vals:
		call_api(test_client, "validators/" + val["id"] + "/", method="DELETE")

	new_vals = call_api(test_client, "validators/")
	assert len(new_vals) == 0


def test_validators(test_client, account_to_check=MAIN_ACCOUNT, network=MAIN_NETWORK):
	test_raz_validators(test_client)

	nfts=call_api(test_client,"nfts/","account="+account_to_check+"&network="+network)
	nft=random_from(nfts)
	col_id=nft["collection"]["id"]

	body = {"validator_name": "validateur_test", "ask_for": col_id, "network": network}
	rc = call_api(test_client, "validators/", "", body=body, method="POST", message="Enregistrement d'un validateur")
	assert "access_code" in rc
	assert len(rc["addresses"]) > 0
	l_valid_addresses=rc["addresses"]

	vals = call_api(test_client, "validators/", "Récupérer les validateurs")
	assert len(vals) == 1

	access_code=rc["access_code"]
	rc = call_api(test_client, "scan_for_access/", body={"validator":access_code , "address": account_to_check})
	assert rc == {"message": "ok"},"Impossible de notifier le validateur"
	assert account_to_check in l_valid_addresses




def test_get_minerpool(test_client):
	pool = call_api(test_client, "minerpool/")
	assert pool is not None
	return len(pool)


def test_create_collection(test_client, name="", miner=MAIN_MINER, network=MAIN_NETWORK,
                           options="canFreeze,canChangeOwner,canUpgrade,canTransferNFTCreateRole,canPause"):
	"""
  :param test_client:
  :param name:
  :param miner:
  :param network:
  :return:
  """
	if len(name) == 0: name = "testcol" + now("hex").replace("0x", "")
	miner = random_from(get_network_instance(network).get_keys()) if miner is None else get_key_by_name(get_network_instance(network).get_keys(),MAIN_MINER)

	if type(miner)==str:miner={"address":miner}
	body = {
		"options": options,
		"name": name,
		"miner":miner.__dict__
	}
	rc = call_api(test_client, "create_collection/", "network=" + network, body)
	assert not rc is None, "La collection n'est pas créer"
	assert rc["cost"] > 0
	assert rc["collection"]["owner"] == miner.address, "La collection n'appartient pas a son propriétaire théorique"
	return rc["collection"]


def test_raz_mintpool(test_client):
	log("Effacement de la pool")
	rc = call_api(test_client, "mintpool/", method="DELETE")
	assert rc == {"deleted": "all"}
	asks = call_api(test_client, "mintpool/")
	assert len(asks) == 0



def test_mintpool(test_client, dest=MAIN_ACCOUNT,  target_network=MAIN_NETWORK,source_network="db-server-nfluent_test"):
	"""
  test de la pool de minage
  :param test_client:
  :param src:
  :param miner:
  :param dest:
  :param network:
  :return:
  """
	test_raz_mintpool(test_client)

	miner:Key=random_from(get_network_instance(target_network).get_keys())
	col = random_from(test_api_get_collections(test_client, target_network, miner.address))

	#nft_id,col_id=test_lazymint(test_client,source_network,cols[0]["id"])

	log("Ajout d'un NFT dans la pool de minage")
	body = {
		"sources": [Mintpool.create_source(miner=random_from(get_network_instance(source_network).get_keys()),network=source_network)],
		"target":Mintpool.create_target(miner=miner,network=target_network,owner=dest,collection=col["id"]),
		"wallet": ""
	}
	ask = call_api(test_client, "add_task_to_mintpool/", body=body)
	assert ask["message"] == "ok"
	assert len(ask["ask_id"]) >0

	log("Vérification que la demande NFT à bien été ajouté dans la mintpool")
	treatments = call_api(test_client, "mintpool/")
	assert len(treatments)==1
	assert treatments[0]["message"]==""

	rc = call_api(test_client, "async_mint/1/")
	assert rc["message"]=="ok"
	rc=rc["n_treated_ask"]

	assert rc == 1

	asks = call_api(test_client, "mintpool/")
	assert len(asks) == 1
	assert asks[0]["message"].startswith("Ok")
	return asks[0]







def test_complete_sc1(test_client, network=MAIN_NETWORK, seuil=10):
	# Choix d'un mineur qui à un solde suffisant
	miner = get_account_from_network(test_client, network, seuil)
	assert not miner is None, "Aucun mineur n'a le solde requis de " + str(seuil)
	miner = miner["address"]

	col = test_create_collection(test_client, "", miner, network)
	assert col is not None, "Impossible de créer la collection"
	col_id = col["id"]

	nfts = test_nfts_from_collection(test_client, col_id, network)
	assert len(nfts) == 0, "La collection ne devrait pas avoir de NFT"

	nft_id, col_id = test_api_mint(test_client, miner, col_id, network)
	assert not nft_id is None

	nfts = test_nfts_from_collection(test_client, col_id, network)
	assert len(nfts) == 1





def mint_collection(test_client, target_network=MAIN_NETWORK):
	"""
	test le minage d'une collection vers target_network
	:param test_client:
	:param target_network:
	:return:
	"""
	col = test_generate_collection(limit=3)
	miner = get_account_from_network(test_client, target_network, seuil=1)
	collection_name = "testCol" + random_from("ABCDEFGHIJKLMNOP",5)
	collection = test_create_collection(test_client, collection_name, miner, target_network)
	log("Consulter la collection "+get_network_instance(MAIN_NETWORK) + collection["id"])
	# for filename in col:
	# 	if filename.endswith("webp"):
	# 		test_mint_from_file(test_client, filename, miner, target_network, col_id=collection["id"])


# def test_mint_collection_to_database():
# 	images=test_generate_collection(limit=3)
# 	col=test_api_get_collections(test_client,network=MAIN_NETWORK,col_or_account=MAIN_ACCOUNT)
# 	assert not col is None

def test_encrypt_keys(test_client):
	for network in NETWORKS:
		log("Encryptage de clé sur le réseau "+network)
		key:Key=random_from(get_network_instance(network).get_keys())
		rc=call_api(test_client,"encrypt_key/"+key.name+"/"+key.secret_key+"/"+key.network+"/")
		assert not rc is None
		assert len(rc["encrypt"])>0



def test_get_account(test_client,addr=MAIN_ACCOUNT,network=MAIN_NETWORK):
	_account=get_network_instance(network).get_account(addr)
	assert not _account is None
	assert "balance" in _account.__dict__
	assert "address" in _account.__dict__
	assert "amount" in _account.__dict__
	return _account


def test_get_account_for_networks(test_client,networks=NETWORKS):
	for network in networks:
		addr=MAIN_ACCOUNTS[network.split("-")[0]]
		test_get_account(test_client,addr,network)