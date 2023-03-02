import time
from random import randint

from flaskr.Polygon import Polygon
from flaskr.Tools import random_from
from flaskr.apptools import get_storage_instance
from tests.test_tools import get_main_account_for_network, create_nft


def test_get_account(addr=None):
	if addr is None:addr=get_main_account_for_network("polygon")
	rc=Polygon("devnet").get_account(addr)
	assert not rc is None
	assert len(rc.address)>0
	assert rc.unity=="MATIC"
	assert rc.balance>=0
	return rc

def test_get_collections(addr=None):
	if addr is None:addr=get_main_account_for_network("polygon")
	rc=Polygon("devnet").get_collections(addr)
	assert not rc is None
	assert len(rc)>0
	return rc







def test_mint(miner="admin",title="MonNFTdeTest"):
	_polygon=Polygon("devnet")
	admin=_polygon.get_key_with_name(miner)
	assert _polygon.get_balance(admin.address)>0
	_data=_polygon.opensea_metadata(from_nft=create_nft(name=title))

	rc=_polygon.mint(miner=admin,title=title,storage=get_storage_instance(),_metadata=_data)
	assert not rc is None
	assert rc["error"]=="", rc["error"]
	assert len(rc["tx"])>0
	assert len(rc["result"]["mint"])>0

	time.sleep(2)
	nfts=_polygon.get_nfts(miner)
	assert rc["result"]["mint"] in [nft.address for nft in nfts],"On ne retrouve pas le NFT miné dans le compte de "+miner

	return rc




def test_get_nfts_from_account(addr:str="admin"):
	_polygon=Polygon("devnet")
	nfts=_polygon.get_nfts(addr,with_attr=False)
	assert not nfts is None
	assert random_from(nfts).owner==_polygon.toAccount(addr).address
	return nfts

def test_transfer(_to:str="sophie",addr:str="",_from="admin"):
	if len(addr)==0:
		nfts=test_get_nfts_from_account(_from)
		assert len(nfts)>0, "Aucun NFT disponible pour "+_from
		nft=nfts[randint(0,len(nfts)-1)]
		addr=nft.address

	_polygon=Polygon("devnet")
	rc=_polygon.transfer(addr,_to)
	assert rc, "Transfer aborted"



