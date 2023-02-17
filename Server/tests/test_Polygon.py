from random import randint

from flaskr.Polygon import Polygon
from flaskr.apptools import get_storage_instance
from tests.test_tools import get_main_account_for_network, create_nft


def test_get_account(addr=None):
	if addr is None:addr=get_main_account_for_network("polygon")
	rc=Polygon("devnet").get_account(addr)
	assert not rc is None
	assert "secret_key" in rc
	return rc

def test_get_account_with_name(name="sophie"):
	test_get_account(name)


def test_mint(title="MonNFTdeTest"):
	_polygon=Polygon("devnet")
	admin=_polygon.get_account("admin")
	assert admin["amount"]>0
	_data=_polygon.opensea_metadata(from_nft=create_nft(name=title))

	rc=_polygon.mint(miner=admin,title=title,storage=get_storage_instance(),_metadata=_data)
	assert not rc is None
	assert rc["error"]=="", rc["error"]
	assert len(rc["tx"])>0
	assert len(rc["result"]["mint"])>0

	return rc




def test_get_nfts_from_account(addr:str="admin"):
	_polygon=Polygon("devnet")
	nfts=_polygon.get_nfts(addr,with_attr=False)
	assert not nfts is None
	return nfts

def test_transfer(_to:str="sophie",addr:str="",_from="admin"):
	if len(addr)==0:
		nfts=test_get_nfts_from_account(_from)
		nft=nfts[randint(0,len(nfts)-1)]
		addr=nft.address

	_polygon=Polygon("devnet")
	rc=_polygon.transfer(addr,_to)
	assert rc, "Transfer aborted"



