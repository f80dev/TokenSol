from flaskr.apptools import get_storage_instance

DOMAIN_SERVER="http://127.0.0.1:4242/"
platforms=[("nftstorage",""),("dao",DOMAIN_SERVER),("file-test",DOMAIN_SERVER)]

#TODO: ajouter les autres plateforms de stockage serveur, github, storej

def test_add():
	obj={"content":"test"}
	for name in platforms:
		storage=get_storage_instance(name[0],name[1])
		cid=storage.add(obj)
		assert "cid" in cid
		assert "url" in cid
		obj_copy=storage.get(cid["cid"])
		assert obj == obj_copy
		rc=storage.rem(cid["cid"])
		assert rc


