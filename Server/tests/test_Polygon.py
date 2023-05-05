import time
from random import randint

from flaskr.Polygon import Polygon
from flaskr.Tools import log, random_from
from flaskr.apptools import get_storage_instance
from tests.test_tools import get_main_account_for_network, create_nft


def test_get_account(addr=None):
	if addr is None:addr=get_main_account_for_network("polygon")
	rc=Polygon("devnet").get_account(addr)
	assert not rc is None
	assert len(rc.address)>0
	assert rc.unity=="matic"
	assert rc.balance>=0
	return rc

def test_get_collections(addr=None):
	if addr is None:addr=get_main_account_for_network("polygon")
	rc=Polygon("devnet").get_collections(addr)
	assert not rc is None
	return rc



def test_mint(miner="admin",title="MonNFTdeTest",
              description="ceci est une description assez longue du NFT pour mesurer sa capacité à absorber des gros fichiers",
              quantity=2):
	_polygon=Polygon("devnet")
	_miner=_polygon.find_key(miner)
	assert _polygon.get_account(_miner.address).balance > 0
	_nft=create_nft(name=title,description=description)
	_data=_polygon.opensea_metadata(from_nft=_nft)

	rc=_polygon.mint(miner=_miner,title=title,storage=get_storage_instance("nftstorage"),_metadata=_data,quantity=quantity)
	assert not rc is None,"La plateforme de storage ne répond pas"
	assert rc["error"]=="", rc["error"]
	assert len(rc["tx"])>0
	assert len(rc["result"]["mint"])>0

	time.sleep(20)
	assert _polygon.has_nft(owner=_miner.address,nft_addr=rc["result"]["mint"]), "On ne retrouve pas le NFT miné dans le compte de "+miner

	_nft=_polygon.get_nft(rc["result"]["mint"]+"-0")
	assert _nft.description==description
	assert _nft.supply==quantity
	assert _polygon.get_balances(_miner.address,rc["result"]["mint"])[rc["result"]["mint"]]==quantity

	return rc


def test_get_balances(addr="admin"):
	_polygon=Polygon("devnet")
	key=_polygon.find_key(addr)
	nfts=_polygon.get_nfts(addr,limit=2)
	rc=_polygon.get_balances(key.address,nfts[0].address)
	assert not rc is None




def test_get_nfts_from_account(addr:str="admin",with_attr=False,limit=30):
	_polygon=Polygon("devnet")
	key=_polygon.find_key(addr)
	log("Recherche des NFTs de "+_polygon.getExplorer(key.address))
	nfts=_polygon.get_nfts(key.address,with_attr=with_attr,limit=limit)
	log(str(len(nfts))+" NFT trouvés")
	assert not nfts is None
	for nft in nfts:
		assert nft.owner==key.address
		assert nft.supply>0

	return nfts


def test_transfer(addr:str="admin"):
	_polygon=Polygon("devnet")
	key=_polygon.find_key(addr)
	dest=_polygon.create_account("paul.dudule@gmail.com",send_real_email=False)
	nfts=_polygon.get_nfts(key.address,with_attr=False,limit=5)
	nft=random_from(nfts)
	_polygon.transfer(nft.address,key,dest.address,1)
	assert _polygon.get_balances(dest.address, nft.address)[nft.address] >= 1



def test_get_nfts_with_attributes(addr:str="admin"):
	test_get_nfts_from_account(addr,True,5)




