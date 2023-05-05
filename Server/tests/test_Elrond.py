from time import sleep

from flaskr.Elrond import Elrond, DEFAULT_OPTION_FOR_ELROND_COLLECTION
from flaskr.Keys import Key
from flaskr.Tools import random_from, now
from flaskr.apptools import get_storage_instance
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
                   storage=get_storage_instance("nftstorage"),
                   files=[],
                   quantity=quantity,
                   visual=nft.visual)
  assert not rc is None
  assert len(rc["error"])==0,rc["error"]
  assert len(rc["result"]["transaction"])>0
  return rc["result"]["mint"]



def test_add_role(account_to_add:str="",miner=MAIN_ACCOUNT,type_collection="SemiFungible",roles_to_add=None):
  """
  liste des roles : https://docs.multiversx.com/tokens/nft-tokens/#roles
  :param account_to_add:
  :param miner:
  :param type_collection:
  :param roles_to_add:
  :return:
  """


  _net=Elrond("devnet")
  if len(account_to_add)==0: account_to_add=random_from(_net.get_keys()).address

  miner=_net.find_key(miner)
  while account_to_add==miner.address:
    account_to_add: str=random_from(_net.get_keys()).address

  #voir https://docs.multiversx.com/tokens/nft-tokens/#roles
  if not roles_to_add: roles_to_add=random_from(["ESDTRoleNFTBurn","ESDTRoleNFTUpdateAttributes","ESDTRoleNFTAddURI","ESDTTransferRole"])
  col=random_from(_net.get_collections(miner.address, type_collection=type_collection))

  rc=_net.add_account_to_collection(account_to_add,col,owner=miner,roles_to_add=roles_to_add)
  assert rc["status"]=="success"

  sleep(3.0)
  col=_net.get_collection(col["id"])
  assert "roles" in col
  assert account_to_add in [x["address"] for x in col["roles"]]



def test_add_role_to_nftcollection(account_to_add:str="",miner=MAIN_ACCOUNT):
  test_add_role(account_to_add,miner,"NonFungible","ESDTTransferRole")



def test_mint_sft(miner=MAIN_ACCOUNT,quantity=10):
  _network=Elrond("devnet")
  _miner=_network.get_keys(address=miner)[0]
  cols=_network.get_collections(miner, False, type_collection="SemiFungible",special_role="canCreate,canBurn,canAddQuantity")
  if len(cols)==0:
    rc=_network.add_collection(_miner,"MaCol"+now("hex"),options=DEFAULT_OPTION_FOR_ELROND_COLLECTION,type_collection="SemiFungible")
    assert not rc is None
    cols.append(rc)
  nft=test_mint_for_collection(miner,col=cols[0]["id"],quantity=quantity)
  return nft


def test_get_nfts(miner=MAIN_ACCOUNT):
  _network=Elrond("devnet")
  nfts=_network.get_nfts(miner,2000)
  assert not nfts is None
  assert len(nfts)>0
  assert len(nfts[0].address)>0


def test_get_sfts(miner=MAIN_ACCOUNT):
  _network=Elrond("devnet")
  nfts=_network.get_nfts(miner,2000,type_token="SemiFungibleESDT")
  assert not nfts is None
  assert len(nfts)>0
  assert len(nfts[0].address)>0


def test_get_owner_of_nft(miner=MAIN_ACCOUNT):
  _network=Elrond("devnet")
  nfts=_network.get_nfts(miner,2000,type_token="SemiFungibleESDT")
  for nft in nfts:
    owners=_network.get_owners_of_nft(nft.address)
    assert len(owners)>0


def test_get_nft(miner=MAIN_ACCOUNT):
  _network=Elrond("devnet")
  nfts=_network.get_nfts(miner,10)
  for nft in nfts:
    rc=_network.get_nft(nft.address,with_balance=miner)
    assert not rc is None
    assert _network.get_balances(miner,nft.address)[nft.address]>0
    assert rc.supply>0


def test_get_balance_for_nft(miner=MAIN_ACCOUNT):
  _network=Elrond("devnet")
  rc=_network.get_balances(miner)
  assert not rc is None


def test_transfer_sft(miner=MAIN_ACCOUNT):
  _network=Elrond("devnet")
  _miner=_network.get_keys(address=miner)[0]
  _dest:Key=random_from(_network.get_keys())
  nfts=_network.get_nfts(_miner.address,100,type_token="SemiFungible")
  q0=0
  nft=None
  balances=_network.get_balances(miner)
  for nft in nfts:
    q0=balances[nft.address]
    if q0>2: break

  if q0<2:
    nft0=test_mint_sft(_miner.address,quantity=10)
    q0=_network.get_balances(miner, nft0.address)[nft0.address]
  else:
    nft0=nft

  tx=_network.transfer(nft0.address,_miner,_dest.address,quantity=1)
  assert len(tx["error"])==0,"Le transfert de "+nft0.address+" vers "+_dest.address+" n'a pas fonctionné"
  q1=_network.get_balances(miner, nft0.address)[nft0.address]
  assert q0-q1==1,"Les quantités ne sont pas cohérentes"




def test_in_collections(col:str=MAIN_COLLECTION,miner=MAIN_ACCOUNT,special_role="canCreate"):
  _network=Elrond("devnet")
  cols=_network.get_collections(miner,False,special_role=special_role)
  assert col in [x["id"] for x in cols], "La collection "+_network.getExplorer(col,"collections")+" n'appartient pas à "+_network.getExplorer(miner,"address")


def test_add_sft_collection(miner=MAIN_ACCOUNT):
  _network=Elrond("devnet")
  _miner=_network.get_keys(address=miner)[0]
  rc=_network.add_collection(_miner,"MaCol"+now("hex"),options=DEFAULT_OPTION_FOR_ELROND_COLLECTION,type_collection="SemiFungible")
  test_in_collections(rc["id"],miner)



def test_account_storage(miner=MAIN_ACCOUNT):
  _network=Elrond("devnet")
  data={"email":"paul.dudule@gmail.com"}
  _miner=_network.find_key(miner)
  #t=_network.save_data_to_account(_miner,data)
  # assert not t is None
  # assert len(t["error"])==0,"Erreur sur la mise a jour "+t["error"]
  rc=_network.get_data_from_account(_miner.address)
  for k in data.keys():
    assert k in rc
    assert rc[k]==data[k]