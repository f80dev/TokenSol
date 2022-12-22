import pytest

from flaskr.secret import SECRET_JWT_KEY
from flaskr import create_app, log
from flaskr.settings import TEMP_DIR, STATIC_FOLDER
from flaskr.NFT import NFT

MAIN_ACCOUNT = "erd1ty3ga9qvmjhwkvh78vwzlm4yvtea9kdu4x4l2ylrnapkzlmn766qdrzdwt"  # bob
MAIN_NETWORK = "elrond-devnet"
MAIN_EMAIL = "paul.dudule@gmail.com"
MAIN_COLLECTION = "NFLUENTA-af9ddf"
DB_NETWORK = "db-cloud-test"

TEMP_TEST_DIR="./tests/temp/"
RESSOURCE_TEST_DIR="./tests/ressources/"


def get_nft(name: str, collection: str,visual="https://hips.hearstapps.com/hmg-prod/images/birthday-cake-decorated-with-colorful-sprinkles-and-royalty-free-image-1653509348.jpg"):
  return NFT(name, symbol="",
             collection={"id": collection},
             attributes={"birthday": "04/02/1971"},
             description="le NFR de mon anniversaire",
             visual=visual
             )


def get_account(test_client, network=MAIN_NETWORK, seuil=1, filter="bob,carol,dan,eve,frank,grace"):
  """Retourne un compte avec au moins x egld"""
  if network.startswith("db-"):network="elrond-devnet"
  with_balance = "false" if seuil == 0 else "true"
  accounts = call_api(test_client, "keys/", "with_balance=" + with_balance + "&network=" + network)
  rc=None
  for account in accounts:
    if account["balance"] >= seuil and (len(filter) == 0 or account["name"] in filter):
      rc=account
      break

  log("Pas de compte disponible disposant d'un solde supérieur au solde")
  return rc


def call_api(test_client,url, params="", body=None, method=None, status_must_be=200,message=""):
  if method is None: method = "GET" if body is None else "POST"
  if not url.startswith("/"): url = "/" + url

  url="/api" + url + "?" + params
  if len(message)>0:log(message+" -> "+url)

  if method == "GET": response = test_client.get(url)
  if method == "POST": response = test_client.post(url, json=body)
  if method == "DELETE": response = test_client.delete(url)

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
    "STATIC_FOLDER": STATIC_FOLDER,
    "ACTIVITY_REPORT": "paul.dudule@gmail.com",
    "DB_SERVER": "cloud",
    "DB_NAME": "nfluent_test",
    "UPLOAD_FOLDER": TEMP_DIR,
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

