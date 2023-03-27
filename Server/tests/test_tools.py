import pytest

from flaskr.StoreFile import StoreFile
from flaskr.Tools import generate_svg_from_fields, encrypt, decrypt, open_html_file
from flaskr.apptools import get_network_instance, create_account
from flaskr import create_app, log, DAO
from flaskr.NFT import NFT

MAIN_POLYGON_ACCOUNT="0xa617546acC33A600f128051455e6aD2a628f4a79" #faucet https://mumbaifaucet.com/ et
MAIN_ACCOUNT = "erd1ty3ga9qvmjhwkvh78vwzlm4yvtea9kdu4x4l2ylrnapkzlmn766qdrzdwt"  #nfluent voir http://127.0.0.1:4200/collections?owner=erd1ty3ga9qvmjhwkvh78vwzlm4yvtea9kdu4x4l2ylrnapkzlmn766qdrzdwt&network=elrond-devnet
MAIN_NETWORK = "elrond-devnet"
MAIN_MINER="bob"

NETWORKS=["file-testnet","db-server-nfluent_test","elrond-devnet","polygon-devnet"]
PLATFORMS=["db-server-nfluent_test","nftstorage","file","infura"] #ipfs
MAIN_STORAGE_PLATFORM=PLATFORMS[0]

MAIN_EMAIL = "paul.dudule@gmail.com"
MAIN_COLLECTION = "NFLUENTA-af9ddf"
DB_NETWORK = "db-server-nfluent_test"
MAIN_ACCOUNTS={
  "elrond":MAIN_ACCOUNT,
  "polygon":MAIN_POLYGON_ACCOUNT,
  "db":DAO(network=DB_NETWORK).create_account(MAIN_EMAIL).address,
  "file":StoreFile(network="file-testnet").create_account(MAIN_EMAIL).address
}
DEFAULT_DOMAIN_APPLI="http://127.0.0.1:4200/"
DEFAULT_DOMAIN_SERVER="http://127.0.0.1:4242/"
TEMP_TEST_DIR="./tests/temp/"
RESSOURCE_TEST_DIR="./tests/ressources/"



def create_nft(name: str= "testName", collection:str=MAIN_COLLECTION,owner=MAIN_MINER,quantity=1,
               visual="https://hips.hearstapps.com/hmg-prod/images/birthday-cake-decorated-with-colorful-sprinkles-and-royalty-free-image-1653509348.jpg",
               description="ceci est la description du NFT",files=["https://nfluent.io"]) -> NFT:
  return NFT(name,
             symbol="",
             collection={"id":collection},
             attributes=[{"birthday": "04/02/1971"}],
             files=files,
             description=description,
             visual=visual,
             marketplace={"quantity":quantity,"price":0}
             )


def test_open_html_file():
  rc=open_html_file("https://nfluent.io/assets/new_account.html",{})
  assert not rc is None


def test_explorer(networks=NETWORKS):
  for network in networks:
    url=get_network_instance(network).getExplorer()
    assert not url is None


def test_generate_svg_from_field():
  with open(RESSOURCE_TEST_DIR+"/voeux2023.svg","r") as file:
    rc=generate_svg_from_fields(file.read())
    assert len(rc)==15
    assert ">Herv" in rc[0]

  with open(RESSOURCE_TEST_DIR+"/svg1.svg","r") as file:
    rc=generate_svg_from_fields(file.read())
    assert len(rc)==1


def test_keys_from_network(test_client, networks=NETWORKS):
  for network in networks:
    _network=get_network_instance(network)
    rc=_network.get_keys()
    assert len(rc)>0


# def test_transfer_extra_network(networks=NETWORKS):
#   for from_network in networks:
#     for target_network in networks:
#       _from_network=get_network_instance(from_network)
#       from_network_miner:Key=random_from(_from_network.get_keys())
#       nft:NFT=random_from(_from_network.get_nfts(from_network_miner.address))
#
#       old_owner=nft.owner
#
#       assert not nft is None
#
#       _target_network=get_network_instance(target_network)
#       target_network_owner=random_from(_target_network.get_keys())
#       rc=transfer(nft.address,from_network_miner=from_network_miner,target_network_miner=target_network_owner,from_network=from_network,target_network=target_network)
#
#       assert not rc is None
#       if target_network!=from_network:
#         assert not nft.address in [x.address for x in _from_network.get_nfts()]
#         assert nft.address in [x.address for x in _target_network.get_nfts()]
#       else:
#         assert _target_network.get_nft(nft.address).owner!=old_owner
#
#
#


def call_api(test_client,url, params="", body=None, method=None, status_must_be=200,message=""):
  if method is None: method = "GET" if body is None else "POST"
  if not url.startswith("/"): url = "/" + url

  url="/api" + url + ("?" + params if len(params)>0 else "")
  if len(message)>0:log(message+" -> "+url)

  if method == "GET": response = test_client.get(url)
  if method == "POST": response = test_client.post(url, json=body)
  if method == "DELETE": response = test_client.delete(url)

  assert response.status_code == status_must_be

  format=response.headers[0][1] if response.headers[0][0]=="Content-Type" else "text/json"

  if "json" in format:
    return response.json
  else:
    return response.data

import config

@pytest.fixture
def test_app():
  # config = {
  #   "DEBUG": True,  # some Flask specific configs
  #   "CACHE_TYPE": "SimpleCache",  # Flask-Caching related configs
  #   "CACHE_DEFAULT_TIMEOUT": 300,
  #   "APPLICATION_ROOT": "http://127.0.0.1:4242",
  #   "DOMAIN_APPLI": "http://127.0.0.1:4200",
  #   "DOMAIN_SERVER": "http://127.0.0.1:4242",
  #   "STATIC_FOLDER": RESSOURCE_TEST_DIR,
  #   "ACTIVITY_REPORT": "paul.dudule@gmail.com",
  #   "DB_SERVER": "cloud",
  #   "DB_NAME": "nfluent_test",
  #   "UPLOAD_FOLDER": TEMP_TEST_DIR,
  #   "JWT_SECRET_KEY": SECRET_JWT_KEY
  # }
  new_config=config.testConfig()
  test_app, scheduler = create_app(new_config)
  test_app.config.update({"TESTING": True, })

  yield test_app


@pytest.fixture
def test_client(test_app):
  with test_app.test_client() as testing_client:
    with test_app.app_context():
      yield testing_client


@pytest.fixture()
def runner(test_app):
  return test_app.test_cli_runner()


def get_main_account_for_network(network:str):
  rc=MAIN_ACCOUNTS[network.split("-")[0]]
  _net=get_network_instance(network)
  if _net.get_account(rc) is None: rc=create_account(MAIN_EMAIL,network)
  return rc

def test_encrypt(message="coucou les amis, voici mon message"):
  assert decrypt(encrypt(message))==message
  assert decrypt(decrypt(encrypt(encrypt(message))))==message

  assert encrypt(message)!=encrypt(message)
  assert encrypt(message,short_code=6)==encrypt(message,short_code=6)
  assert len(encrypt(message,short_code=6))==6


