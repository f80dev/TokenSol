from flaskr.Elrond import Elrond
from flaskr.Tools import random_from, now
from tests.test_tools import MAIN_ACCOUNT, create_nft, MAIN_COLLECTION


def test_get_collections():
	_net=Elrond("devnet")
	for k in _net.get_keys():
		miner=k.address
		for col in _net.get_collections(miner):
			assert "roles" in col
			assert "owner" in col
			assert "timestamp" in col
			assert "type" in col
			assert "name" in col
			for role in col["roles"]:
				assert "address" in role
				assert "canCreate" in role
				assert "canBurn" in role
				assert "canAddQuantity" in role
				assert "canAddUri" in role
				assert "canUpdateAttributes" in role


def test_add_role_to_nftcollection(account_to_add:str="",miner=MAIN_ACCOUNT):
	test_add_role(account_to_add,miner,"NonFungible","ESDTTransferRole")

def test_add_role(account_to_add:str="",miner=MAIN_ACCOUNT,type_collection="SemiFungible",roles_to_add="ESDTRoleNFTCreate"):
	"""
	liste des roles : https://docs.multiversx.com/tokens/nft-tokens/#roles
	:param account_to_add:
	:param miner:
	:param type_collection:
	:param roles_to_add:
	:return:
	"""
	_net=Elrond("devnet")
	if len(account_to_add)==0:
		account_to_add=random_from(_net.get_keys()).address
	miner=_net.find_key(miner)
	while account_to_add==miner.address: account_to_add=random_from(_net.get_keys()).address

	col=random_from(_net.get_collections(miner.address, type_collection=type_collection))
	rc=_net.add_account_to_collection(account_to_add,col, miner,roles_to_add=roles_to_add)
	assert rc["status"]=="success"

	col=_net.get_collection(col["id"])
	assert "roles" in col
	assert account_to_add in [x["address"] for x in col["roles"]]



def test_mint_sft(miner=MAIN_ACCOUNT):
	_network=Elrond("devnet")
	_miner=_network.get_keys(address=miner)[0]
	cols=_network.get_collections(miner, False, type_collection="SemiFungible",special_role="canCreate")
	if len(cols)==0:
		rc=_network.add_collection(_miner,"MaCol"+now("hex"),type_collection="SemiFungible")
		assert not rc is None
		cols.append(rc)
	test_mint_for_collection(miner,cols[0]["id"],2)


def test_in_collections(col:str=MAIN_COLLECTION,miner=MAIN_ACCOUNT,special_role="canCreate"):
	_network=Elrond("devnet")
	cols=_network.get_collections(miner,False,special_role=special_role)
	assert col in [x["id"] for x in cols], "La collection "+_network.getExplorer(col,"collections")+" n'appartient pas à "+_network.getExplorer(miner,"address")


def test_add_sft_collection(miner=MAIN_ACCOUNT):
	_network=Elrond("devnet")
	_miner=_network.get_keys(address=miner)[0]
	rc=_network.add_collection(_miner,"MaCol"+now("hex"),type_collection="SemiFungible")
	test_in_collections(rc["id"],miner)


def test_mint_for_collection(miner=MAIN_ACCOUNT,col=MAIN_COLLECTION,quantity=1):
	_network=Elrond("devnet")
	nft=create_nft(collection=col)
	_miner=_network.get_keys(address=miner)[0]

	test_in_collections(col,miner)

	rc=_network.mint(miner=_miner,
	                 title="TestNFT",
	                 description=nft.description,
	                 collection={"id":col},
	                 properties=[],
	                 storage="nftstorage",
	                 files=[],
	                 quantity=quantity)
	assert not rc is None
	assert len(rc["error"])==0,rc["error"]
	assert len(rc["result"]["transaction"])>0
	return rc["result"]["mint"]


