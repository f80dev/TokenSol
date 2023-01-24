import pytest

from flaskr import log
from flaskr.ipfs import IPFS
from flaskr.settings import IPFS_SERVER
from tests.test_tools import RESSOURCE_TEST_DIR


@pytest.fixture
def ipfs():
	return IPFS(IPFS_SERVER)

def test_add(ipfs):
	cid=ipfs.add({"test":"coucou"})
	assert "Hash" in cid

def test_add_file(ipfs,f="batch_importation.xlsx"):
	#with open(RESSOURCE_TEST_DIR+f,"rb") as file: bytes=file.read()
	cid=ipfs.add_file(RESSOURCE_TEST_DIR+f)
	assert "url" in cid
	assert "Hash" in cid
	assert "filename" in cid
	log("téléchargement possible sur "+cid["url"])


