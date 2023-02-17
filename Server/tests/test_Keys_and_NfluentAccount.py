from flaskr.Keys import Key
from flaskr.NFluentAccount import NfluentAccount


def test_nfluentaccount_constructor():
	nfaccount=NfluentAccount(address="blablabla",balance=10)
	assert not nfaccount is None

