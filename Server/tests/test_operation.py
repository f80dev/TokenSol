from flaskr.apptools import get_nfts_from_src, async_mint
from tests.test_tools import *

def test_nfts_from_operation(test_client,operation="Main_devnet"):
  rc=call_api(test_client,"nfts_from_operation/"+operation+"/")
  assert not rc is None
  assert "sources" in rc
  assert "nfts" in rc

def test_operations(test_client):
  rc=call_api(test_client,"operations/")
  assert len(rc)>0



def test_get_nfts_from_src(test_client,network="elrond-devnet",owner="bob"):
  src={"active":True,"type":"database","dbname":"test","connexion":"web3"}
  nfts=get_nfts_from_src(src)
  assert nfts is not None
  #assert len(nfts)>0,"Aucun nft trouvé dans la source database"

  src={"active":True,"type":"network","connexion":network,"owner":owner}
  nfts=get_nfts_from_src(src)
  assert len(nfts)>0

