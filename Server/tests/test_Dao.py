import pytest

from flaskr import log, DAO
from flaskr.NFT import NFT
from flaskr.apptools import get_network_instance
from tests.test_tools import DB_NETWORK

MAIN_DB_ACCOUNT="sophie.dudule@gmail.com"
MAIN_ADDR_ACCOUNT="db_5d9ec5ad02166612bb708c00eeb2da55433880a55b892dc2754392b4d3f15eb6"

@pytest.fixture
def db():
	return get_network_instance(DB_NETWORK)

def test_reset(db:DAO):
	db.reset()

def test_add_key(db:DAO,email=MAIN_DB_ACCOUNT):
	db.reset("keys")
	account=db.create_account(email=email)
	log("L'address du compte est "+account.address)
	assert len(db.get_keys())==1
	return account

def test_create_account(db:DAO,email=MAIN_DB_ACCOUNT):
	db.reset("accounts")
	account=db.create_account(email=email)
	assert len(account.address)>0
	assert len(account.name)>0
	return account

def test_mint(db:DAO,miner=None,description="description",supply=10) -> NFT:
	if miner is None: miner=db.get_account(MAIN_ADDR_ACCOUNT)
	assert not miner is None
	tx=db.mint(miner,"titre NFT",description,{"id":"macollect"},[],"ipfs",[],supply,0)

	_nft=db.get_nft(tx["result"]["mint"])
	assert len(_nft.address)>0
	assert _nft.miner==miner.address
	assert _nft.description==description
	assert db.get_balances(miner.address,_nft.address)==supply
	return _nft

def test_burn(db:DAO):
	miner=db.get_account(MAIN_ADDR_ACCOUNT)
	if miner is None: miner=test_create_account("paul.dudule@gmail.com")
	nft:NFT=test_mint(db,miner)
	before=db.get_balances(miner.address,nft.address)
	db.burn(nft.address,miner,3)
	after=db.get_balances(miner.address,nft.address)
	assert before-after==3

