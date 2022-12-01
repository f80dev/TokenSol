import pytest

from flaskr.secret import SECRET_JWT_KEY
from flaskr import create_app
from flaskr.settings import TEMP_DIR
from flaskr.NFT import NFT

MAIN_ACCOUNT = "erd1ty3ga9qvmjhwkvh78vwzlm4yvtea9kdu4x4l2ylrnapkzlmn766qdrzdwt"  # bob
MAIN_NETWORK = "elrond-devnet"
MAIN_COLLECTION = "NFLUENTA-af9ddf"
DB_NETWORK = "db-cloud-test"


def get_nft(name: str, collection: str,visual="https://hips.hearstapps.com/hmg-prod/images/birthday-cake-decorated-with-colorful-sprinkles-and-royalty-free-image-1653509348.jpg"):
  return NFT(name, symbol="",
             collection={"id": collection},
             attributes={"birthday": "04/02/1971"},
             description="le NFR de mon anniversaire",
             visual=visual
             )

def get_account(test_client, network=MAIN_NETWORK, seuil=1, filter="bob,carol,dan,eve,frank,grace"):
  """Retourne un compte avec au moins x egld"""
  with_balance = "false" if seuil == 0 else "true"
  accounts = call_api(test_client, "keys/", "with_balance=" + with_balance + "&network=" + network)
  for account in accounts:
    if account["balance"] >= seuil and (len(filter) == 0 or account["name"] in filter): return account
  return None

def call_api(test_client,url, params="", body=None, method=None, status_must_be=200):
  if not url.startswith("/"): url = "/" + url
  if method is None: method = "GET" if body is None else "POST"

  if method == "GET": response = test_client.get("/api" + url + "?" + params)
  if method == "POST": response = test_client.post("/api" + url + "?" + params, json=body)
  if method == "DELETE": response = test_client.delete("/api" + url + "?" + params)

  assert response.status_code == status_must_be
  return response.json



@pytest.fixture
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

  yield test_app


@pytest.fixture
def test_client(test_app):
  with test_app.test_client() as testing_client:
    with test_app.app_context():
      yield testing_client


@pytest.fixture()
def runner(test_app):
  return test_app.test_cli_runner()

