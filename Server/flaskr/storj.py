import base64
import json

from flaskr.Storage import Storage
from uplink_python import uplink, upload, access

from flaskr.secret import STORJ_API_KEY, STORJ_SATTELITE_ADDR, STORJ_PASSPHRASE

"""
L'usage de Storj nécéssite l'installation de go:  https://go.dev/doc/install
Voir la documentation générale : https://storj-thirdparty.github.io/uplink-python/#/

"""

class Storj(Storage):
	def __init__(self,bucket_name="tokenforge"):
		self.bucket=bucket_name
		self.access=uplink.Uplink().request_access_with_passphrase(STORJ_API_KEY,STORJ_SATTELITE_ADDR,STORJ_PASSPHRASE)
		self.client=self.access.open_project()



	def add(self,content) -> dict:
		"""
		voir https://storj-thirdparty.github.io/uplink-python/uplink_python.uplink.html
		:param content:
		:return:
		"""
		if type(content)==dict:
			content=json.dumps(content)

		if type(content)==str:
			if "base64" in content:content=base64.b64decode(content.split("base64,")[1])

		rc=self.client.upload_object(self.bucket,"")

		return {"cid":rc}

	def add_file(self,file):
		f=open(file,"r")
		rc=self.client.write_file(f,len(f))
		f.close()
		return rc

