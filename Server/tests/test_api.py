import random

#import pytest
from flaskr.Tools import get_operation, now
#from tests.test_tools import call_api, MAIN_NETWORK, MAIN_COLLECTION, MAIN_ACCOUNT

from test_tools import *

@pytest.fixture()
def operation():
  return get_operation("Main_devnet")


def test_getyaml(test_client):
  rc = call_api(test_client, "getyaml/Main_devnet/", "dir=../Operations")
  assert rc["id"] == "Main_devnet"


def test_api_get_collections(test_client, network=MAIN_NETWORK, col_or_account=MAIN_COLLECTION):
  rc = call_api(test_client, "collections/" + col_or_account + "/", "network=" + network + "&with_detail=true")
  assert not rc is None
  return rc


def test_api_get_collections_for_main_account(test_client, network=MAIN_NETWORK):
  rc = test_api_get_collections(test_client, network, MAIN_ACCOUNT)
  assert len(rc) > 0
  assert rc[0]["collection"] == "NFLUENTA-af9ddf"
  return rc[0]["collection"]


def test_infos(test_client):
  rc = call_api(test_client, "infos/")
  assert "Server" in rc


def test_keys(test_client, network=MAIN_NETWORK):
  rc = get_account(test_client, network, 1)
  assert rc["balance"] >= 1

  rc = get_account(test_client, network, 0)
  assert rc is not None

  rc = get_account(test_client, network, 1000000000)
  assert rc is None


def test_nfts_from_collection(test_client, col_id="", network=MAIN_NETWORK):
  if col_id == "":
    cols = test_api_get_collections(test_client, network)
    col_id = cols[0]["id"]

  rc = call_api(test_client, "nfts_from_collection/" + col_id + "/", "network=" + network)
  assert not rc is None
  return rc


def test_nfts_from_owner(test_client, owner=MAIN_ACCOUNT, network=MAIN_NETWORK):
  """
  Récupére les nfts d'une collection ou d'un client
  :param test_client:
  :return:
  """
  if owner == "":
    account = get_account(test_client, network=network, seuil=1)
    owner = account["pubkey"]

  rc = call_api(test_client, "nfts/", "account=" + owner + "&network=" + network)
  assert len(rc) > 0

  return rc


def find_collection_to_mint(test_client, miner):
  cols = call_api(test_client, "collections/" + miner + "/", "filter_type=NonFungibleESDT")
  if len(cols) > 0:
    col_id = None
    for col in cols:
      if not col_id:
        for role in col["roles"]:
          if role["canCreate"] and miner == role["address"]:
            col_id = col["collection"]
            return col_id
  return None


def test_api_mint(test_client, miner="", col_id=MAIN_COLLECTION, network=MAIN_NETWORK) -> (str, str):
  if col_id == "":
    col_id = find_collection_to_mint(test_client, miner)

  if miner == "" and not "db-" in network:
    cols = test_api_get_collections(test_client, network, col_id)
    assert len(cols) > 0, "La collection " + col_id + " est introuvable"
    miner = cols[0]["owner"]

  if col_id:
    _nft = get_nft("test_" + now("hex"), col_id)
    rc = call_api(test_client, "mint/",
                  params="keyfile=" + miner + "&network=" + network,
                  body=_nft.__dict__,
                  method="POST")
    assert not rc is None
    assert len(rc["error"]) == 0, rc["error"]
    assert "mint" in rc["result"]

    token_id = rc["result"]["mint"]
    return token_id, col_id


def test_lazymint(test_client, network=DB_NETWORK) -> (str, str):
  nft_id, col_id = test_api_mint(test_client, network=network)
  assert not nft_id is None
  return nft_id, col_id


def test_transfer_from_lazymint(test_client, miner=MAIN_ACCOUNT, to_network=MAIN_NETWORK, from_network=DB_NETWORK,
                                dest=""):
  nft_id, col_id = test_lazymint(test_client)
  rc = test_transfer_to(test_client, to_network=to_network, from_network=from_network, miner=miner, token_id=nft_id,
                        dest=dest)
  assert not rc is None


def test_transfer_to(test_client, from_network=MAIN_NETWORK, to_network=MAIN_NETWORK, miner="", token_id="", dest=""):
  if token_id == "":
    token_id, col_id = test_api_mint(test_client, miner=miner, network=to_network)

  if dest == "":
    for account in call_api(test_client, "keys/"):
      if account["pubkey"] != dest:
        dest = account["pubkey"]
        break

  if miner == "":
    rc = call_api(test_client, "transfer_to/" + token_id + "/" + dest + "/",
                  "from_network=" + from_network + "&to_network=" + to_network, method="POST")
  else:
    rc = call_api(test_client, "transfer_to/" + token_id + "/" + dest + "/" + miner + "/",
                  "from_network=" + from_network + "&to_network=" + to_network, method="POST")

  assert not rc is None
  assert len(rc["error"]) == 0

  nfts = call_api(test_client, "nfts/", "account=" + dest + "&network=" + to_network + "&limit=2000")
  assert rc["token_id"] in [nft["address"] for nft in nfts]


def test_raz_validators(test_client):
  vals = call_api(test_client, "validators/")
  for val in vals:
    call_api(test_client, "validators/" + val["id"] + "/", method="DELETE")

  new_vals = call_api(test_client, "validators/")
  assert len(new_vals) == 0


def test_validators(test_client, account_to_check=MAIN_ACCOUNT, network=MAIN_NETWORK):
  test_raz_validators(test_client)

  cols = test_api_get_collections(test_client, network=network, col_or_account=account_to_check)
  col_id = cols[random.randint(0, len(cols) - 1)]["id"]

  body = {"validator_name": "validateur_test", "ask_for": col_id, "network": MAIN_NETWORK}
  rc = call_api(test_client, "validators/", "", body=body, method="POST")
  assert "access_code" in rc
  assert len(rc["addresses"]) > 0

  vals = call_api(test_client, "validators/")
  assert len(vals) == 1

  rc = call_api(test_client, "check_access_code/" + bytes(rc["access_code"], "utf8"))
  assert len(rc) > 0


def test_get_minerpool(test_client):
  pool = call_api(test_client, "minerpool/")
  if len(pool) > 0:
    token = pool[0]


def test_create_collection(test_client, name="", miner=MAIN_ACCOUNT, network=MAIN_NETWORK,
                           options="canFreeze,canChangeOwner,canUpgrade,canTransferNFTCreateRole,canPause"):
  """
  :param test_client:
  :param name:
  :param miner:
  :param network:
  :return:
  """
  if len(name) == 0: name = "testcol" + now("hex").replace("0x", "")
  if miner is None: miner = get_account(test_client, network, 1)
  body = {
    "options": options,
    "name": name
  }
  rc = call_api(test_client, "create_collection/" + miner + "/", "network=" + network, body)
  assert not rc is None
  assert rc["cost"] > 0
  assert rc["collection"]["owner"] == miner
  return rc["collection"]


def test_complete_sc1(test_client, network=MAIN_NETWORK, seuil=1):
  miner = get_account(test_client, network, seuil)
  assert not miner is None, "Aucun mineur n'a le solde requis de " + str(seuil)
  miner = miner["pubkey"]

  col = test_create_collection(test_client, "", miner, network)
  assert col is not None, "Impossible de créer la collection"
  col_id = col["id"]

  nfts = test_nfts_from_collection(test_client, col_id, network)
  assert len(nfts) == 0, "La collection ne devrait pas avoir de NFT"

  nft_id, col_id = test_api_mint(test_client, miner, col_id, network)
  assert not nft_id is None

  nfts = test_nfts_from_collection(test_client, col_id, network)
  assert len(nfts) == 1



