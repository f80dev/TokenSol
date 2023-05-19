import base64
import json

from flaskr.Storage import Storage
from uplink_python import uplink, upload, access

from flaskr.secret import STORJ_API_KEY, STORJ_SATTELITE_ADDR, STORJ_PASSPHRASE, STORJ_SECRETKEY, STORJ_ENDPOINT

"""
L'usage de Storj nécéssite l'installation de go:  https://go.dev/doc/install
Voir la documentation générale : https://storj-thirdparty.github.io/uplink-python/#/
voir https://www.storj.io/blog/reading-and-writing-files-from-to-storj-with-pandas
"""

class Storj(Storage):
	def __init__(self,bucket_name="tokenforge"):
		self.bucket=bucket_name
		#Obtenir les identifiants
		self.storage_options= {
			'key': STORJ_API_KEY,
			'secret': STORJ_SECRETKEY,
			'client_kwargs': {'endpoint_url': STORJ_ENDPOINT}
		}



	def add(self,content,overwrite=False) -> dict:
		"""
		voir https://storj-thirdparty.github.io/uplink-python/uplink_python.uplink.html
		:param content:
		:return:
		"""
		if type(content)==dict:
			content=json.dumps(content)

		if type(content)==str:
			if "base64" in content:content=base64.b64decode(content.split("base64,")[1])

		return {"cid":""}

	def add_file(self,file):
		f=open(file,"r")
		rc=self.client.write_file(f,len(f))
		f.close()
		return rc

