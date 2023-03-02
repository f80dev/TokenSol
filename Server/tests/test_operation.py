from flaskr.apptools import get_nfts_from_src
from tests.test_tools import *

def test_nfts_from_operation(test_client,operation="Main_devnet"):
  rc=call_api(test_client,"nfts_from_operation/"+operation+"/")
  assert not rc is None
  assert "sources" in rc
  assert "nfts" in rc

def test_operations(test_client):
  rc=call_api(test_client,"operations/")
  assert len(rc)>0



def test_get_nfts_from_src(test_client,network=MAIN_NETWORK,owner=MAIN_ACCOUNT):
  src={"active":True,"type":"database","dbname":"test","connexion":"server"}
  nfts=get_nfts_from_src(src)
  assert nfts is not None
  #assert len(nfts)>0,"Aucun nft trouvé dans la source database"

  src={"active":True,"type":"database","dbname":"test","connexion":"server","filter":{"collection":"MACOLLEC-4356f0"}}
  nfts=get_nfts_from_src(src)
  assert not nfts is None

  src={"active":True,"type":"network","connexion":network,"filter":{"owner":owner}}
  nfts=get_nfts_from_src(src)
  assert len(nfts)>0

