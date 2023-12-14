import random
from time import sleep

from flaskr.Elrond import Elrond, DEFAULT_OPTION_FOR_ELROND_COLLECTION, DEFAULT_ROLE_FOR_SFT, DEFAULT_ROLE_FOR_NFT
from flaskr.Keys import Key
from flaskr.NFT import NFT
from flaskr.Tools import random_from, now, log, hex_to_str
from flaskr.apptools import get_storage_instance
from tests.test_tools import MAIN_ACCOUNT, create_nft, MAIN_COLLECTION, MAIN_MINER

NETWORK_TO_USE="devnet"

def init_network(miner_addr:str=MAIN_MINER,collection_name="macollection"):
  _network=Elrond(NETWORK_TO_USE)
  collection=test_create_collection(miner_addr,collection_name,"SemiFungible")
  log("collection créé: " + collection["id"])


def test_mint_nft(miner_addr=MAIN_MINER,collection="",quantity=1,simulation=False):
  _network=Elrond(NETWORK_TO_USE)
  if len(collection)==0:
    collection=test_get_collections(account=miner_addr)[0]
    collection=collection["id"]
  nft=create_nft(collection=collection,miner=_network.get_keys(address=miner_addr)[0])
  nft.supply=quantity

  #test_in_collections(col,miner)
  t=_network.mint(nft=nft,storage=get_storage_instance("nftstorage"))
  rc=_network.send_transaction(t,nft.miner,simulation=simulation)

  assert not rc is None
  assert len(rc["error"])==0,rc["error"]
  assert len(rc["results"]["ESDTNFTCreate"])>0

  nft_address=hex_to_str(rc["results"]["ESDTNFTCreate"][0])+"-"+rc["results"]["ESDTNFTCreate"][1]
  return _network.get_nft(nft_address)



def test_get_collections(account=MAIN_ACCOUNT,n_cols=1):
  _network=Elrond(NETWORK_TO_USE)
  _account=_network.get_keys(address=account)[0]
  cols=_network.get_collections(_account,detail=False)
  assert len(cols)>=n_cols
  return cols


def old_test_get_collections_from_all_account():
  _net=Elrond(NETWORK_TO_USE)
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




def test_get_nfts_from_collection(col=MAIN_COLLECTION):
  _network=Elrond(NETWORK_TO_USE)
  nfts=_network.get_nfts_from_collections([col],False)
  for nft in nfts:
    assert len(nft.balances.keys())>0
  return nfts





def test_add_role(account_to_add:str="",miner=MAIN_ACCOUNT,collection="",roles_to_add=None):
  """
  liste des roles : https://docs.multiversx.com/tokens/nft-tokens/#roles
  :param account_to_add:
  :param miner:
  :param type_collection:
  :param roles_to_add:
  :return:
  """

  _net=Elrond(NETWORK_TO_USE)
  miner=_net.find_key(miner)

  if len(account_to_add)==0:
    account_to_add=random_from(_net.get_keys()).address
    while account_to_add==miner.address:
      account_to_add: str=random_from(_net.get_keys()).address

  #voir https://docs.multiversx.com/tokens/nft-tokens/#roles
  roles_to_add=roles_to_add or random_from(DEFAULT_ROLE_FOR_NFT.split(","))
  if collection=="":
    _col=random_from(_net.get_collections(miner.address))
  else:
    _col=_net.get_collection(collection)

  type_collection=_col["type"]
  t=_net.add_account_to_collection(account_to_add=account_to_add,
                                    collection_id=_col["id"],
                                    owner=miner.address,
                                    roles_to_add=DEFAULT_ROLE_FOR_SFT if "SemiFungible" in type_collection else DEFAULT_ROLE_FOR_NFT)
  rc=_net.send_transaction(t,miner)
  assert rc["status"]=="success"
  sleep(3.0)
  roles=_net.get_roles_for_collection(_col["id"],account_to_add)
  assert len(roles["roles"])>0
  return roles



# def test_add_role_to_nftcollection(account_to_add:str="",miner=MAIN_ACCOUNT):
#   test_add_role(account_to_add,miner,"NonFungible","ESDTTransferRole")


def test_create_token(name="mytoken",miner=MAIN_MINER):
  _network=Elrond(NETWORK_TO_USE)
  _miner=_network.get_keys(address=miner)[0]
  t=_network.create_token(name,_miner)
  rc=_network.send_transaction(t,_miner)
  assert rc["error"]==""
  assert "issue" in rc["results"]
  return rc["results"]["issue"][0]


def test_create_collection_and_mint_and_transfer(miner=MAIN_MINER,dest=MAIN_ACCOUNT):
  _network=Elrond(NETWORK_TO_USE)
  col=test_create_collection(miner,"")
  sleep(10)
  _col=_network.get_collection(col["id"])

  test_mint_nft(miner,collection=_col["id"])
  sleep(10)
  nfts=test_get_nfts_from_collection(_col["id"])
  assert len(nfts)==1

  rc=test_transfer_nft(nfts[0].address,miner,dest)
  assert rc["error"]==""


def test_transfer_nft(nft_addr:str="",miner_addr=MAIN_MINER,dest_addr=MAIN_ACCOUNT):
  _network=Elrond(NETWORK_TO_USE)
  _miner=_network.find_key(miner_addr)
  dest_addr=_network.find_key(dest_addr).address
  if nft_addr=="":
    nfts=_network.get_nfts(_miner.address,type_token="NonFungibleESDT")
    if len(nfts)==0:
      test_mint_nft(_miner.address)
      nfts=_network.get_nfts(_miner.address,type_token="NonFungibleESDT")

    assert len(nfts)>0
    nft:NFT=nfts[random.randint(0,len(nfts)-1)]
    log("Tentative de transfert de "+nft.explorer())
    nft_addr=nft.address
  _t=_network.transfer(nft_addr,_miner.address,dest_addr)

  nb_nfts_before=len(_network.get_nfts(dest_addr,type_token="NonFungibleESDT"))
  rc=_network.send_transaction(_t,_miner)
  assert rc["error"]==""

  sleep(12)
  nb_nfts_after=len(_network.get_nfts(dest_addr,type_token="NonFungibleESDT"))
  assert nb_nfts_after-nb_nfts_before==1
  return rc


def test_get_accounts():
  _network=Elrond(NETWORK_TO_USE)
  for acc in _network.get_keys():
    balance=_network.get_balance(acc.address)
    log(acc.name+" ("+acc.address+") dispose de "+str(balance)+" egld")
    assert not balance is None



def test_transfert_egld(token_id="egld",quantity=1):
  _network=Elrond(NETWORK_TO_USE)
  _bank=_network.get_keys(address=MAIN_MINER)[0]
  for k in _network.get_keys():
    if k.address!=_bank.address:
      balance_before=_network.get_balance(k.address,token_id)
      t=_network.transfer_money(token_id,_bank,k.address,quantity)
      rc=_network.send_transaction(t,_bank,timeout=100)
      assert rc["error"]==""
      sleep(5)
      balance_after=_network.get_balance(k.address,token_id)
      assert balance_after-balance_before==quantity





def test_create_collection(miner=MAIN_ACCOUNT,collection_name="",type_collection="NonFungible",simulation=False,owner_role=DEFAULT_ROLE_FOR_NFT) -> dict:
  _network=Elrond(NETWORK_TO_USE)
  _miner=_network.get_keys(address=miner)[0]
  if collection_name=="":collection_name="MaCol"+now("hex")
  t=_network.add_collection(_miner,collection_name,options=DEFAULT_OPTION_FOR_ELROND_COLLECTION,type_collection=type_collection)
  rc=_network.send_transaction(t,_miner,simulation=simulation,timeout=200)
  col_id=rc["results"]["issue"+type_collection][0]

  assert not rc is None
  assert rc["error"]==""
  sleep(8.0)

  roles=test_add_role(_miner.address,_miner,col_id,roles_to_add=owner_role)

  return {"id":rc["results"]["issue"+type_collection][0],"roles":roles}


def test_mint_sft(miner=MAIN_MINER,quantity=10,force_create_collection=False,simulation=False,type_collection="SemiFungible"):
  _network=Elrond(NETWORK_TO_USE)
  _miner=_network.get_keys(address=miner)[0]
  cols=_network.get_collections(miner, False, type_collection=type_collection) if not force_create_collection else []
  if len(cols)==0 and not simulation:
    cols.append(test_create_collection(_miner.address,"",type_collection=type_collection))
  return test_mint_nft(_miner.address,collection=cols[0]["id"],quantity=quantity,simulation=simulation)


def test_create_SFTCollection_and_mint():
  test_mint_sft(force_create_collection=True)


def test_find_esdt_by_owner(owner=MAIN_ACCOUNT):
  rc=Elrond(NETWORK_TO_USE).get_tokens(owner)
  assert len(rc)>1
  assert "identifier" in rc[0]

def test_find_esdt_by_name():
  rc=Elrond(NETWORK_TO_USE).get_tokens(filter="BTC")
  assert len(rc)>=100
  assert "image" in rc[0]


def test_get_nfts(miner=MAIN_ACCOUNT):
  _network=Elrond(NETWORK_TO_USE)
  nfts=_network.get_nfts(_network.find_key(miner),2000)
  assert not nfts is None
  assert len(nfts)>0
  assert nfts[0].balances[miner]>0
  assert len(nfts[0].address)>0


def test_get_sfts(miner=MAIN_ACCOUNT):
  _network=Elrond(NETWORK_TO_USE)
  nfts=_network.get_nfts(_network.find_key(miner),2000,type_token="SemiFungibleESDT")
  assert not nfts is None
  assert len(nfts)>0
  assert nfts[0].balances[_network.find_key(miner)]>0
  assert len(nfts[0].address)>0


def test_get_owner_of_nft(miner=MAIN_ACCOUNT):
  _network=Elrond(NETWORK_TO_USE)
  nfts=_network.get_nfts(miner,2000,type_token="SemiFungibleESDT")
  for nft in nfts:
    owners=_network.get_owners_of_nft(nft.address)
    assert len(owners)>0


def test_get_nft(miner=MAIN_ACCOUNT):
  _network=Elrond(NETWORK_TO_USE)
  nfts=_network.get_nfts(miner,10)
  for nft in nfts:
    rc=_network.get_nft(nft.address,with_balance_for=_network.find_key(miner))
    assert not rc is None
    assert rc.supply>0


def test_get_balance_for_nft(miner=MAIN_ACCOUNT):
  _network=Elrond(NETWORK_TO_USE)
  rc=_network.get_balances(miner)
  assert not rc is None


def test_transfer_sft(miner=MAIN_ACCOUNT):
  _network=Elrond(NETWORK_TO_USE)
  miner=_network.find_key(miner).address
  _miner=_network.find_key(miner)
  _dest:Key=random_from(_network.get_keys())
  nfts=_network.get_nfts(miner,100,type_token="SemiFungible")
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

  t=_network.transfer(nft0.address,miner,_dest.address,quantity=1)
  tx=_network.send_transaction(t,_miner)

  assert len(tx["error"])==0,"Le transfert de "+nft0.address+" vers "+_dest.address+" n'a pas fonctionné"
  q1=_network.get_balances(miner)[nft0.address]
  assert q0-q1==1,"Les quantités ne sont pas cohérentes"




def test_in_collections(col:str=MAIN_COLLECTION,miner=MAIN_ACCOUNT,special_role="canCreate"):
  _network=Elrond(NETWORK_TO_USE)
  cols=_network.get_collections(miner,False,special_role=special_role)
  assert col in [x["id"] for x in cols], "La collection "+_network.getExplorer(col,"collections")+" n'appartient pas à "+_network.getExplorer(miner,"address")


def test_add_sft_collection(miner=MAIN_ACCOUNT,type_collection="SemiFungible"):
  _network=Elrond(NETWORK_TO_USE)
  _miner=_network.find_key(miner)
  t=_network.add_collection(_miner.address,"MaCol"+now("hex"),options=DEFAULT_OPTION_FOR_ELROND_COLLECTION,type_collection=type_collection)
  rc=_network.send_transaction(t,_miner)
  assert rc["error"]==""
  col_id=rc["results"]["issue"+type_collection][0]
  test_in_collections(col_id,miner)



def test_account_storage(miner=MAIN_ACCOUNT):
  _network=Elrond(NETWORK_TO_USE)
  data={"email":"paul.dudule@gmail.com"}
  _miner=_network.find_key(miner)
  #t=_network.save_data_to_account(_miner,data)
  # assert not t is None
  # assert len(t["error"])==0,"Erreur sur la mise a jour "+t["error"]
  rc=_network.get_data_from_account(_miner.address)
  for k in data.keys():
    assert k in rc
    assert rc[k]==data[k]