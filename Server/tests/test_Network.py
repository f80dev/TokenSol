from flaskr import log
from flaskr.Keys import Key
from flaskr.TokenForge import upload_on_platform
from flaskr.Tools import random_from, now
from flaskr.apptools import get_network_instance, mint, create_account
from tests.test_art import PLATFORM_LIST
from tests.test_tools import NETWORKS, create_nft, MAIN_ACCOUNTS, DEFAULT_DOMAIN_APPLI, MAIN_EMAIL, RESSOURCE_TEST_DIR, \
	PLATFORMS, DEFAULT_DOMAIN_SERVER


def test_get_keys(networks=NETWORKS):
	for network in networks:
		bl=get_network_instance(network)
		keys=bl.get_keys()
		assert not keys is None


def test_get_nfts(networks=NETWORKS):
	nfts=[]
	for network in networks:
		bl=get_network_instance(network)
		for i in range(20):
			owner=random_from(bl.get_keys())
			nfts=bl.get_nfts(owner.address)
			assert not nfts is None
			# if len(nfts)>0:
			# 	assert random_from(nfts).owner==owner.address,"Probleme d'attribution du propriétaire pour "+network
			# 	break
		#assert len(nfts)>0

	return nfts




def test_get_nft(networks=NETWORKS):
	for network in networks:
		log("Network="+network)
		bl=get_network_instance(network)
		owner=None
		for owner in bl.get_keys():
			nfts=bl.get_nfts(owner.address)
			if len(nfts)>0: break

		nft=bl.get_nft(random_from(nfts).address)

		assert not nft is None
		assert nft.owner==owner.address
		assert len(nft.miner)>0



def test_mint(networks=NETWORKS,platform=PLATFORMS[0],miner=None):
	nft=None
	for network in networks:
		_network=get_network_instance(network)
		_network.reset("nfts")
		log("Travail sur "+str(_network))
		owner=MAIN_ACCOUNTS[_network.network_name]
		if miner is None:miner=random_from(_network.get_keys())
		collections=get_network_instance(network).get_collections(miner.address,detail=False)
		col=random_from(collections)
		if col:
			collection_id=col["id"] if "id" in col else col["name"]
		else:
			collection_id=""

		nft=create_nft(collection=collection_id)
		rc=mint(nft,miner=miner,owner=owner,network=_network,offchaindata_platform=platform,price=0)
		assert not rc is None
		assert len(rc["error"])==0

		nft=_network.get_nft(rc["result"]["mint"])
		assert not nft is None
		miner=None

	return nft



def test_transfer(networks=NETWORKS):
	for network in networks:
		_network=get_network_instance(network)
		miner:Key=random_from(_network.get_keys())
		nfts=_network.get_nfts(miner.address)
		if len(nfts)==0:
			test_mint([network],miner=miner)
			nfts=_network.get_nfts(miner.address)

		nft=random_from(nfts)
		email="paul.dudule"+str(now("hex"))+"@gmail.com"
		dest=test_create_account(email,[network])
		_network.transfer(nft.address,miner,dest.address)

		assert len(_network.get_nfts(dest.address))==1



def test_create_account(email=MAIN_EMAIL,networks=NETWORKS,domain_appli=DEFAULT_DOMAIN_APPLI):
	rc=None
	for network in networks:
		log("Travail sur "+network)
		rc=create_account(email,network,domain_appli=domain_appli,
		               dao=None,mail_new_wallet=RESSOURCE_TEST_DIR+"new_wallet",
		               mail_existing_wallet=RESSOURCE_TEST_DIR+"existing_wallet",send_real_email=False)
		assert not rc is None
		assert len(rc.address)>0
		assert len(rc.secret_key)>0
		assert len(rc.name)>0
	return rc


def test_all_platform_with_json(platforms=PLATFORM_LIST):
	doc={"description":"ma description","title":"my title"}
	for platform in platforms:
		rc=upload_on_platform(doc,platform,domain_server=DEFAULT_DOMAIN_SERVER)
		assert len(rc["url"])>0
		assert len(rc["cid"])>0

