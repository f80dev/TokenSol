import requests

from flaskr import log
from flaskr.apptools import get_storage_instance
from tests.test_art import get_image
from tests.test_tools import RESSOURCE_TEST_DIR

DOMAIN_SERVER="http://127.0.0.1:4242/"
PLATFORMS=[
	("githubstorage", "github-nfluentdev-storage_2-main"),
	("dao", DOMAIN_SERVER),
	("nftstorage", "")
]

#a inclure quand terminé : ("megaupload","tests"),	("storj","tests"),

#TODO: ajouter les autres plateforms de stockage serveur, github, storej

def test_add_object():
	obj={"content":"test"}
	for name in PLATFORMS:
		storage=get_storage_instance(name[0],name[1])
		cid=storage.add(obj)
		assert "cid" in cid
		assert "url" in cid
		obj_copy=storage.get(cid["cid"])
		assert obj == obj_copy
		rc=storage.rem(cid["cid"])
		assert rc


def test_add_file():
	for name in PLATFORMS:
		log("Test de la plateforme "+name[0])

		with open(RESSOURCE_TEST_DIR+"/CV.docx","rb") as hFile:
			file=hFile.read()

			storage=get_storage_instance(name[0],name[1])
			result=storage.add(file,overwrite=True)
			assert len(result["hash"])>0
			assert len(result["cid"])>0
			assert len(result["url"])>0


def test_clear_directory(platform=PLATFORMS[0]):
	#voir la liste des platforms:
	storage=get_storage_instance(platform[0],platform[1])
	files=storage.list()
	for f in files:
		storage.rem(f["cid"],sha=f["sha"])

def test_add_image():
	img=""
	while not img.startswith("http"):
		img=get_image(section="backgrounds")

	bytes=requests.get(img).content

	for name in PLATFORMS:
		log("Test de la plateforme "+name[0])
		storage=get_storage_instance(name[0],name[1])
		cid=storage.add(img,overwrite=True)
		result=requests.get(cid["url"]).content
		assert result==bytes,"Les images "+img+" n'est pas bien stocké sur "+name[0]
