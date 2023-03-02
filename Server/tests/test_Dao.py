from flaskr.apptools import get_network_instance
from tests.test_tools import DB_NETWORK


def test_reset():
	get_network_instance(DB_NETWORK).reset()


def test_add_key(email="sophie.dudule@gmail.com"):
	_db_network=get_network_instance(DB_NETWORK)
	_db_network.reset("keys")
	_db_network.create_account(email=email)
	assert len(_db_network.get_keys())==1