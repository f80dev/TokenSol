import pytest

from flaskr.storj import Storj

@pytest.fixture
def storj():
	return Storj()

def test_add(storj):
	storj.add({"test":"coucou"})
	assert False
