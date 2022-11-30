import random

import pytest
from flaskr import create_app
from flaskr.NFT import NFT
from flaskr.settings import TEMP_DIR
from flaskr.secret import SECRET_JWT_KEY
from flaskr.Tools import get_operation, now


@pytest.fixture()
def operation():
  return get_operation("Main_devnet")


def get_nft(name: str, collection: str, visual="https://hips.hearstapps.com/hmg-prod/images/birthday-cake-decorated-with-colorful-sprinkles-and-royalty-free-image-1653509348.jpg"):
  return NFT(name, symbol="",
             collection={"id": collection},
             attributes={"birthday": "04/02/1971"},
             description="le NFR de mon anniversaire",
             visual=visual
             )




@pytest.fixture()
def test_app():
  config = {
    "DEBUG": True,  # some Flask specific configs
    "CACHE_TYPE": "SimpleCache",  # Flask-Caching related configs
    "CACHE_DEFAULT_TIMEOUT": 300,
    "APPLICATION_ROOT": "http://127.0.0.1:4242",
    "DOMAIN_APPLI": "http://127.0.0.1:4200",
    "DOMAIN_SERVER": "http://127.0.0.1:4242",
    "ACTIVITY_REPORT": "paul.dudule@gmail.com",
    "DB_SERVER": "web3",
    "DB_NAME": "nfluent_test",
    "UPDLOAD_FOLDER": TEMP_DIR,
    "JWT_SECRET_KEY": SECRET_JWT_KEY
  }
  test_app, scheduler = create_app(config)
  test_app.config.update({"TESTING": True, })
  # other setup can go here
  yield test_app
  # clean up / reset resources here


@pytest.fixture()
def test_client(test_app):
  with test_app.test_client() as testing_client:
    with test_app.app_context():
      yield testing_client


@pytest.fixture()
def runner(test_app):
  return test_app.test_cli_runner()


def call_api(test_client, url, params="", body=None, method="GET", status_must_be=200):
  if not url.startswith("/"): url = "/" + url
  if method == "GET": response = test_client.get("/api" + url + "?" + params)
  if method == "POST":
    response = test_client.post("/api" + url + "?" + params, json=body)
  assert response.status_code == status_must_be
  return response.json


def test_getyaml(test_client):
  rc = call_api(test_client, "getyaml/Main_devnet/?dir=../Operations")
  assert rc["id"] == "Main_devnet"


def test_api_get_collections(test_client):
  rc = call_api(test_client, "collections/erd1z7gemgj4sumlaqs8aquahntszmx3hxde35yahhc705qst5xnhj0q42yhfh/")
  assert rc[0]["id"] == 'VENTEIAA-cd1447'


def test_infos(test_client):
  rc = call_api(test_client, "infos/")
  assert "Server" in rc


def test_get_nft_from_db(test_client):
  rc = call_api(test_client, "get_nft_from_db/")
  assert False


def test_keys(test_client):
  rc = call_api(test_client, "keys/", "network=elrond-devnet")
  assert len(rc) > 0


def test_nfts(test_client):
  rc = call_api(test_client, "nfts/", "network=elrond-devnet")
  assert len(rc) > 0


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


def test_api_mint(test_client):
  keys = call_api(test_client, "keys/", "network=elrond-devnet&with_balance=true")
  for key in keys:
    if key["balance"] > 0:
      miner = key["pubkey"]
      col_id = find_collection_to_mint(test_client, miner)

      if col_id:
        _nft = get_nft("test_" + now("hex"), col_id)
        rc = call_api(test_client, "mint/",
                      params="keyfile=" + miner + "&network=elrond-devnet",
                      body=_nft.__dict__,
                      method="POST")
        assert not rc is None
        assert len(rc["error"]) == 0
        assert "mint" in rc["result"]

        token_id = rc["result"]["mint"]
        nfts = call_api(test_client, "nfts/", "account=" + miner + "&network=elrond-devnet")
        assert token_id in [nft["address"] for nft in nfts]
        return token_id,miner


def test_transfer_to(test_client):
  token_id,miner=test_api_mint(test_client)

  dests=call_api(test_client,"keys/")
  dest=dests[random.randint(0,len(dests))]["pubkey"]

  rc=call_api(test_client,"transfer_to/"+token_id+"/"+dest+"/"+miner+"/","network=elrond-devnet",method="POST")
  assert not rc is None
  assert len(rc["error"]) == 0

  nfts = call_api(test_client, "nfts/", "account=" + dest + "&network=elrond-devnet")
  assert token_id in [nft["address"] for nft in nfts]

