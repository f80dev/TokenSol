import pytest

from flaskr.storj import Storj

@pytest.fixture
def storj():
	return Storj()

def test_add(storj):
	storj.blank_test()
