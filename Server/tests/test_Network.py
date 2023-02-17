from flaskr import log
from flaskr.Tools import random_from
from flaskr.apptools import get_network_instance, mint, create_account
from tests.test_tools import NETWORKS, create_nft, MAIN_ACCOUNTS, DEFAULT_DOMAIN_APPLI, MAIN_EMAIL, RESSOURCE_TEST_DIR, \
	PLATFORMS


def test_get_keys(networks=NETWORKS):
	for network in networks:
		bl=get_network_instance(network)
		keys=bl.get_keys()
		assert not keys is None


def test_get_nfts(networks=NETWORKS):
	for network in networks:
		bl=get_network_instance(network)
		owner=random_from(bl.get_keys())
		nfts=bl.get_nfts(owner.address)

		assert not nfts is None
		assert random_from(nfts).owner==owner.address,"Probleme d'attribution du propriétaire pour "+network


def test_get_nft(networks=NETWORKS):
	for network in networks:
		bl=get_network_instance(network)
		owner=None
		for owner in bl.get_keys():
			nfts=bl.get_nfts(owner.address)
			if len(nfts)>0: break

		nft=bl.get_nft(random_from(nfts).address)

		assert not nft is None
		assert nft.owner==owner.address
		assert len(nft.miner)>0








def test_mint(networks=NETWORKS,platform=PLATFORMS[0]):
	nft=None
	for network in networks:
		_network=get_network_instance(network)
		_network.reset("nfts")
		log("Travail sur "+str(_network))
		owner=MAIN_ACCOUNTS[_network.network_name]
		miner=random_from(_network.get_keys())
		collections=get_network_instance(network).get_collections(miner.address,detail=False)
		collection_id=random_from(collections)["id"] if len(collections)>0 else ""
		nft=create_nft(collection=collection_id)
		rc=mint(nft,miner=miner,owner=owner,network=_network,offchaindata_platform=platform,price=0)
		assert not rc is None
		assert len(rc["error"])==0

		nft=_network.get_nft(rc["result"]["mint"])
		assert not nft is None

	return nft



def test_transfer(networks=NETWORKS):
	for network in networks:
		_network=get_network_instance(network)
		miner=_network.get_keys()[0]
		nfts=_network.get_nfts(miner.address,1)
		if len(nfts)>0:
			key=_network.create_account("paul.dudule@gmail.com",send_real_email=False)
			_network.transfer(nfts[0].address,miner,key.address)

			finded=False
			for nft in _network.get_nfts(key.address,10):
				if nft.address==nfts[0].address:
					finded=True
					break
			assert finded,"NFT non trouvé"



def test_create_account(email=MAIN_EMAIL,networks=NETWORKS,domain_appli=DEFAULT_DOMAIN_APPLI):
	for network in networks:
		log("Travail sur "+network)
		rc=create_account(email,network,domain_appli=domain_appli,
		               dao=None,mail_new_wallet=RESSOURCE_TEST_DIR+"new_wallet",
		               mail_existing_wallet=RESSOURCE_TEST_DIR+"existing_wallet")
		assert len(rc)>0


