from flaskr.Elrond import Elrond
from tests.test_tools import MAIN_ACCOUNT, create_nft


def test_mint_for_collection(miner=MAIN_ACCOUNT,col="TESTCOLF-efa3c3"):
	_network=Elrond("devnet")
	nft=create_nft(collection=col)
	_miner=_network.get_keys(address=miner)[0]

	cols=_network.get_collections(miner,False)
	assert col in [x["collection"] for x in cols],"La collection "+col+" n'appartient pas à "+miner

	rc=_network.mint(miner=_miner,title="TestNFT",description=nft.description,collection={"id":col},properties=[],storage="nftstorage",files=[])
	assert not rc is None
	assert len(rc["error"])==0
	assert len(rc["result"]["transaction"])>0


