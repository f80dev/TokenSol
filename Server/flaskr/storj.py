import base64
import json

import numpy as np
import pandas as pd

from flaskr.Storage import Storage

from flaskr.secret import STORJ_API_KEY, STORJ_SATTELITE_ADDR, STORJ_PASSPHRASE, STORJ_SECRETKEY, STORJ_ENDPOINT

"""
L'usage de Storj nécéssite l'installation de go:  https://go.dev/doc/install
Voir la documentation générale : https://storj-thirdparty.github.io/uplink-python/#/
voir https://www.storj.io/blog/reading-and-writing-files-from-to-storj-with-pandas
"""

class Storj(Storage):
	def __init__(self,bucket_name="tokenforge",domain_server=""):
		self.bucket=bucket_name
		#Obtenir les identifiants
		self.storage_options= {
			'key': STORJ_API_KEY,
			'secret': STORJ_SECRETKEY,
			'client_kwargs': {'endpoint_url': STORJ_ENDPOINT}
		}


	def blank_test(self):
		#voir la doc de s3fs : https://s3fs.readthedocs.io/en/latest/
		df = pd.DataFrame(np.random.uniform(0,1,[10**3,3]), columns=list('ABC'))

		# Saving as CSV
		result=df.to_csv(f"s3://{self.bucket}/{STORJ_API_KEY}",index=False,storage_options=self.storage_options)
		return result


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

