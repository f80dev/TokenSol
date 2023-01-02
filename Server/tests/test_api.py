import base64
import random
from json import loads

from flaskr.Elrond import Elrond
from flaskr.Polygon import Polygon
from flaskr.Tools import get_operation, now
from flaskr.settings import OPERATIONS_DIR
from tests.test_art import test_generate_collection
from tests.test_tools import *


@pytest.fixture()
def operation():
	return get_operation("Main_devnet")


def test_getyaml(test_client):
	rc = call_api(test_client, "getyaml/Main_devnet/", "dir="+OPERATIONS_DIR)
	assert rc["id"] == "Main_devnet"


def test_api_upload_batch(test_client, file=RESSOURCE_TEST_DIR+"batch_importation.xlsx", miner=MAIN_ACCOUNT):
	rc = call_api(test_client, "upload_batch/", body={"content": file})
	assert not rc is None


def test_api_get_collections(test_client, network=MAIN_NETWORK, col_or_account=MAIN_COLLECTION):
	rc = call_api(test_client, "collections/" + col_or_account + "/", "network=" + network + "&with_detail=true")
	assert not rc is None
	return rc


def test_api_get_collections_for_main_account(test_client, network=MAIN_NETWORK):
	rc = test_api_get_collections(test_client, network, MAIN_ACCOUNT)
	assert len(rc) > 0
	assert 'TESTCOLF-64ad12' in [x["collection"] for x in rc]



def test_infos(test_client):
	rc = call_api(test_client, "infos/")
	assert "Server" in rc


def test_keys_networks(test_client,networks=NETWORKS):
	for network in networks:
		print("Analyse du réseau "+network)
		test_keys(test_client,network,0,"")

def test_keys(test_client, network=MAIN_NETWORK, seuil=1,filter="bob,carol,dan,eve,frank,grace"):
	rc = get_account(test_client, network, 0,filter=filter)
	assert rc is not None, "Aucun compte disponible"

	rc = get_account(test_client, network, seuil=seuil,filter=filter)
	assert rc != None, "Aucun compte disponible avec un solde > " + str(seuil)
	assert rc["balance"] >= seuil

	rc = get_account(test_client, network, seuil=1000000000,filter=filter)
	assert rc is None, "Le solde ne doit pas fonctionner"


def test_create_account_from_email(network=MAIN_NETWORK,email=MAIN_EMAIL):
	if "elrond" in network:rc=Elrond(network).create_account(email=email)
	if "polygon" in network:rc=Polygon(network).create_account(email=email)
	assert not rc is None
	assert len(rc)==4
	assert len(rc[2].split(" "))>10
	assert len(rc[3])>20


def test_nfts_from_collection(test_client, col_id="", network=MAIN_NETWORK):
	if col_id == "":
		cols = test_api_get_collections(test_client, network)
		col_id = cols[0]["id"]

	rc = call_api(test_client, "nfts_from_collection/" + col_id + "/", "network=" + network)
	assert not rc is None
	return rc["nfts"]


def test_nfts_from_owner(test_client, owner=MAIN_ACCOUNT, network=MAIN_NETWORK):
	"""
  Récupére les nfts d'une collection ou d'un client
  :param test_client:
  :return:
  """
	if owner == "":
		account = get_account(test_client, network=network, seuil=1)
		owner = account["pubkey"]

	rc = call_api(test_client, "nfts/", "account=" + owner + "&network=" + network)
	assert len(rc) > 0

	return rc


def find_collection_to_mint(test_client, miner,network="elrond-devnet"):
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


def test_mint_polygon(test_client):
	test_api_mint(test_client,miner=MAIN_POLYGON_ACCOUNT,col_id="",network="polygon-devnet")


def test_api_mint(test_client, miner="", col_id=MAIN_COLLECTION, network=MAIN_NETWORK) -> (str, str):
	if col_id == "":
		col_id = find_collection_to_mint(test_client, miner,network)

	if miner == "" and not "db-" in network:
		cols = test_api_get_collections(test_client, network, col_id)
		assert len(cols) > 0, "La collection " + col_id + " est introuvable"
		miner = cols[0]["owner"]

	if col_id:
		_nft = get_nft("test_" + now("hex"), col_id)
		rc = call_api(test_client, "mint/",
		              params="keyfile=" + miner + "&network=" + network,
		              body=_nft.__dict__,
		              method="POST")
		assert not rc is None
		assert len(rc["error"]) == 0, rc["error"]
		assert "mint" in rc["result"]

		token_id = rc["result"]["mint"]
		return token_id, col_id


def test_lazymint(test_client, network=DB_NETWORK, collection_to_use=MAIN_COLLECTION) -> (str, str):
	"""
  Execute un minage vers la base de données
  :param test_client:
  :param network:
  :return:
  """
	log("Test de creation d'un NFT de la collection " + collection_to_use + " dans " + DB_NETWORK)
	assert "db-" in network, "fonction uniquement valable pour miner dans une base de données"
	nft_id, col_id = test_api_mint(test_client, network=network, col_id=collection_to_use)
	assert not nft_id is None
	assert not col_id is None
	return nft_id, col_id


def test_transfer_from_lazymint(test_client, dest="", miner=MAIN_ACCOUNT, to_network=MAIN_NETWORK,
                                from_network=DB_NETWORK, collection_to_mint=MAIN_COLLECTION):
	nft_id, col_id = test_lazymint(test_client, from_network,
	                               collection_to_use=collection_to_mint)  # Créer un token dans la base de données
	assert not nft_id is None and not col_id is None, "Pas de NFT disponible dans " + collection_to_mint
	rc = test_transfer_to(test_client, to_network=to_network, from_network=from_network, miner=miner, token_id=nft_id,
	                      dest=dest)
	assert rc, "Le transfert n'a pas eu lieu"


def test_transfer_to(test_client, from_network=MAIN_NETWORK, to_network=MAIN_NETWORK, miner="", token_id="", dest=""):
	if token_id == "":
		token_id, col_id = test_api_mint(test_client, miner=miner, network=from_network)

	if dest == "":
		account = get_account(test_client, network=to_network, seuil=0)
		dest = account["pubkey"]

	if miner == "":
		rc = call_api(test_client, "transfer/" + token_id + "/" + dest + "/",
		              "from_network=" + from_network + "&to_network=" + to_network, method="POST")
	else:
		rc = call_api(test_client, "transfer/" + token_id + "/" + dest + "/" + miner + "/",
		              "from_network=" + from_network + "&to_network=" + to_network, method="POST")

	assert not rc is None
	assert len(rc["error"]) == 0
	assert len(rc["token_id"]) > 0
	nfts = call_api(test_client, "nfts/", "account=" + dest + "&network=" + to_network + "&limit=2000")
	assert rc["token_id"] in [nft["address"] for nft in nfts], "Le NFT n'est pas présent dans le wallet du destinataire"

	return True


def test_raz_validators(test_client):
	vals = call_api(test_client, "validators/")
	for val in vals:
		call_api(test_client, "validators/" + val["id"] + "/", method="DELETE")

	new_vals = call_api(test_client, "validators/")
	assert len(new_vals) == 0


def test_validators(test_client, account_to_check=MAIN_ACCOUNT, network=MAIN_NETWORK):
	log("Effacement des validateurs")
	test_raz_validators(test_client)

	cols = test_api_get_collections(test_client, network=network, col_or_account=account_to_check)
	assert len(cols) > 0, "Aucune collection disponible pour le test"
	col_id = cols[random.randint(0, len(cols) - 1)]["id"]

	body = {"validator_name": "validateur_test", "ask_for": col_id, "network": network}
	rc = call_api(test_client, "validators/", "", body=body, method="POST", message="Enregistrement d'un validateur")
	assert "access_code" in rc
	assert len(rc["addresses"]) > 0

	vals = call_api(test_client, "validators/", "Récupérer les validateurs")
	assert len(vals) == 1

	rc = call_api(test_client, "scan_for_access/", body={"validator": rc["access_code"], "address": account_to_check})
	assert rc == {"message": "ok"}


def test_get_minerpool(test_client):
	pool = call_api(test_client, "minerpool/")
	assert pool is not None
	return len(pool)


def test_create_collection(test_client, name="", miner=MAIN_ACCOUNT, network=MAIN_NETWORK,
                           options="canFreeze,canChangeOwner,canUpgrade,canTransferNFTCreateRole,canPause"):
	"""
  :param test_client:
  :param name:
  :param miner:
  :param network:
  :return:
  """
	if len(name) == 0: name = "testcol" + now("hex").replace("0x", "")
	if miner is None: miner = get_account(test_client, network, 1)
	if type(miner)==str:miner={"pubkey":miner}
	body = {
		"options": options,
		"name": name
	}
	rc = call_api(test_client, "create_collection/" + miner["pubkey"] + "/", "network=" + network, body)
	assert not rc is None, "La collection n'est pas créer"
	assert rc["cost"] > 0
	assert rc["collection"]["owner"] == miner["pubkey"], "La collection n'appartient pas a son propriétaire théorique"
	return rc["collection"]


def test_raz_mintpool(test_client):
	log("Effacement de la pool")
	rc = call_api(test_client, "mintpool/", method="DELETE")
	assert rc == {"deleted": "all"}
	asks = call_api(test_client, "mintpool/")
	assert len(asks) == 0


def test_mintpool(test_client, src=None, miner=MAIN_ACCOUNT, dest=MAIN_ACCOUNT, network=MAIN_NETWORK):
	"""
  test de la pool de minage
  :param test_client:
  :param src:
  :param miner:
  :param dest:
  :param network:
  :return:
  """
	cols = test_api_get_collections(test_client, network, miner)
	assert len(cols) > 0

	if src is None:
		src = {"active": True, "type": "database", "dbname": "nfluent_test", "connexion": "web3"}
		nft_id,col_id=test_lazymint(test_client,"db-web3-nfluent_test",cols[0]["id"])

	test_raz_mintpool(test_client)

	log("Ajout d'un NFT dans la pool de minage")
	body = {
		"owner": dest,
		"network": network,
		"miner": miner,
		"sources": [src],
		"collections": cols[0]["id"],
		"wallet": ""
	}
	ask = call_api(test_client, "add_user_for_nft/", body=body)
	assert ask["message"] == "ok"
	assert len(ask["ask_id"]) >0

	log("Vérification que le NFT à bien été ajouté")
	asks = call_api(test_client, "mintpool/")
	assert len(asks) == 1

	rc = call_api(test_client, "async_mint/1/")
	assert rc == {"message":"ok","n_treated_ask":1}

	asks = call_api(test_client, "mintpool/")
	assert len(asks) == 1
	assert asks[0]["message"].startswith("Ok")


def test_complete_sc1(test_client, network=MAIN_NETWORK, seuil=10):
	# Choix d'un mineur qui à un solde suffisant
	miner = get_account(test_client, network, seuil)
	assert not miner is None, "Aucun mineur n'a le solde requis de " + str(seuil)
	miner = miner["pubkey"]

	col = test_create_collection(test_client, "", miner, network)
	assert col is not None, "Impossible de créer la collection"
	col_id = col["id"]

	nfts = test_nfts_from_collection(test_client, col_id, network)
	assert len(nfts) == 0, "La collection ne devrait pas avoir de NFT"

	nft_id, col_id = test_api_mint(test_client, miner, col_id, network)
	assert not nft_id is None

	nfts = test_nfts_from_collection(test_client, col_id, network)
	assert len(nfts) == 1


# def test_async_mint(test_client):
	"""
  test direct de la pool de minage sans passer par l'api
  :param test_client:
  :return:
  """
	# pool = async_mint({}, 1)


def random_from(limit=5):
	s = "ABCDEFGHIJKLOMNOPQRST"
	rc = ""
	while len(rc) < limit:
		rc = rc + s[random.randint(0, len(s) - 1)]
	return rc


def mint_collection(test_client, target_network=MAIN_NETWORK):
	col = test_generate_collection(limit=3)
	miner = get_account(test_client, target_network, seuil=1)
	collection_name = "testCol" + random_from(5)
	collection = test_create_collection(test_client, collection_name, miner, target_network)
	log("Consulter la collection https://devnet-explorer.elrond.com/collections/" + collection["id"])
	# for filename in col:
	# 	if filename.endswith("webp"):
	# 		test_mint_from_file(test_client, filename, miner, target_network, col_id=collection["id"])


