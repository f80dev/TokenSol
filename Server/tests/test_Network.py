from time import sleep

from flaskr import log
from flaskr.Keys import Key
from flaskr.TokenForge import upload_on_platform
from flaskr.Tools import random_from, now
from flaskr.apptools import get_network_instance, mint, create_account
from tests.test_art import PLATFORM_LIST
from tests.test_tools import NETWORKS, create_nft, MAIN_ACCOUNTS, DEFAULT_DOMAIN_APPLI, MAIN_EMAIL, RESSOURCE_TEST_DIR, \
	PLATFORMS, DEFAULT_DOMAIN_SERVER, MAIN_ACCOUNT, MAIN_NETWORK


def test_reset(networks=NETWORKS):
	for network in networks:
		_network=get_network_instance(network)
		if not _network.is_blockchain():
			_network.reset()



def test_transfer(networks=NETWORKS):
	for network in networks:
		_network=get_network_instance(network)
		miner:Key=random_from(_network.get_keys())
		nfts=_network.get_nfts(miner.address)
		if len(nfts)==0:
			test_mint([network],miner=miner,owner=miner.address)
			nfts=_network.get_nfts(miner.address)

		nft=random_from(nfts)

		email="paul.dudule"+str(now("hex"))+"@gmail.com"
		dest=test_create_account(email,[network])
		rc=_network.transfer(nft.address,miner,dest.address)

		if _network.network_name=="polygon": sleep(15.0)
		assert len(_network.get_nfts(dest.address))>0
		assert _network.has_nft(dest.address,nft.address)




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


def test_add_collection(network=MAIN_NETWORK,account=None,type_collection="SemiFungible"):
	_network=get_network_instance(network)
	if account is None:account=MAIN_ACCOUNTS[_network.network_name]
	miner=_network.find_key(account)
	col=_network.add_collection(miner,"MyCol"+now("hex")[4:],type_collection=type_collection)
	if col is None:
		rc=_network.add_account_to_collection(miner.address,col,miner)
		if not "error" in rc:
			return col
	return col

def test_mint(networks=NETWORKS,platform=PLATFORMS[0],miner=None,quantity=1,owner=None):
	nft=None
	for network in networks:
		_network=get_network_instance(network)
		_network.reset("nfts")
		log("Travail sur "+str(_network))
		if owner is None: owner=MAIN_ACCOUNTS[_network.network_name]
		if miner is None:miner=random_from(_network.get_keys())

		type_collection="SemiFungible" if quantity>1 else "NonFungible"
		cols=_network.get_collections(miner.address, detail=False, type_collection=type_collection)

		col=None
		for i in range(len(cols)*3):     #On fait une 20 d'essai
			col:dict=random_from(cols)
			if _network.canMintOnCollection(miner.address,col,quantity): break
		if col is None or not _network.canMintOnCollection(miner.address,col,quantity):
			col:dict=test_add_collection(network,account=miner.address,type_collection=type_collection)

		nft=create_nft(collection=col,quantity=quantity)
		rc=mint(nft,miner=miner,owner=owner,network=_network,offchaindata_platform=platform,price=0)
		assert not rc is None
		assert len(rc["error"])==0

		nft=_network.get_nft(rc["result"]["mint"])
		assert not nft is None

		if _network.is_blockchain():
			if _network.network_name=="polygon": sleep(10.0)
			assert _network.has_nft(owner,nft.address),"On ne retrouve pas "+nft.address+" chez "+_network.getExplorer(owner,"address")
		miner=None

	return nft



def test_get_keys(networks=NETWORKS):
	for network in networks:
		bl=get_network_instance(network)
		keys=bl.get_keys()
		assert not keys is None


def test_get_account(addr=MAIN_ACCOUNT,network=MAIN_NETWORK):
	_account=get_network_instance(network).get_account(addr)
	assert not _account is None
	assert "balance" in _account.__dict__
	assert "address" in _account.__dict__
	assert "amount" in _account.__dict__
	return _account


def test_get_accounts(networks=NETWORKS):
	for network in networks:
		bl=get_network_instance(network)
		accounts=bl.get_accounts()
		assert len(accounts)>0
		assert accounts[0].balance>0
		assert len(accounts[0].address)>0


def test_get_nfts(networks=NETWORKS):
	nfts=[]
	for network in networks:
		bl=get_network_instance(network)
		for i in range(2):
			owner=random_from(bl.get_keys())
			nfts=bl.get_nfts(owner.address,with_attr=False,with_collection=False)
			assert not nfts is None

	return nfts




def test_get_nft(networks=NETWORKS):
	for network in networks:
		log("Network="+network)
		bl=get_network_instance(network)
		owner=None
		for owner in bl.get_keys():
			nfts=bl.get_nfts(owner.address)
			if len(nfts)>0: break

		if len(nfts)>0:
			nft=bl.get_nft(random_from(nfts).address)

			assert not nft is None
			assert nft.owner==owner.address
			assert len(nft.miner)>0



def test_get_collection(networks=NETWORKS):
	for network in networks:
		_network=get_network_instance(network)
		owner=MAIN_ACCOUNTS[_network.network_name]
		cols=_network.get_collections(owner,detail=True)
		if len(cols)>0:
			assert len(cols[0]["id"])>0,"Nom de la collection inconnu"
			# assert len(cols[0]["name"])>0,"Nom de la collection inconnu"
			# assert len(cols[0]["owner"])>0,"La collection doit avoir un propriétaire"








def test_all_platform_with_json(platforms=PLATFORM_LIST):
	doc={"description":"ma description","title":"my title"}
	for platform in platforms:
		rc=upload_on_platform(doc,platform,domain_server=DEFAULT_DOMAIN_SERVER)
		assert len(rc["url"])>0
		assert len(rc["cid"])>0

