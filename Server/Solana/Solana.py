import json
import os
import platform
import subprocess
from datetime import datetime
from os import listdir
from time import sleep

import base58
import requests
from solana.keypair import Keypair

from Tools import log

SOLANA_KEY_DIR="./Solana/Keys/"
METABOSS_DIR="./Server"

class Solana:
	def __init__(self,network="devnet"):
		self.network=network
		self.api="https://api.mainnet-beta.solana.com" if network=="mainnet" else "https://api.devnet.solana.com"


	def exec(self,command:str,param:str="",account:str="",keyfile="admin.json",data=None,sign=False):
		keyfile=keyfile +".json" if not keyfile.endswith(".json") else keyfile
		keyfile="./Keys/"+keyfile if not keyfile.startswith("./Keys") else keyfile

		os.chdir("./Solana")

		file_to_mint="./Temp/to_mint_"+str(datetime.now().timestamp())+".json"
		with open(file_to_mint, 'w') as f:
			f.writelines(json.dumps(data,indent=4, sort_keys=True))
			f.close()

		progname="metaboss-ubuntu-latest" if platform.system()!="Windows" else "metaboss.exe"
		if progname in os.listdir():
			cmd=progname+" "+command+" "+param+" --keypair "+keyfile+" --log-level info -r "+self.api
			if len(account)>0:cmd=cmd+" --account "+account
			cmd=cmd+" --nft-data-file "+file_to_mint+(" --sign" if sign else "")

			log(cmd)
			mes=subprocess.run(cmd,capture_output=True,timeout=10000,shell=True)
			sleep(2.0)
		else:
			log(progname+" non installé")

		rc_error=""
		rc=""
		try:
			if len(mes.stderr)>0:
				rc_error="Execution de "+cmd+" retourne "+str(mes.stderr,"ansi")
			else:
				rc="Ok"
				os.remove(file_to_mint)
		except:
			rc_error="Probléme d'execution"

		os.chdir("..")
		log("error="+rc_error)
		log("result="+rc)

		return {"error":rc_error,"result":rc,"command":cmd}



	def balance(self,user):
		"""
		https://docs.solana.com/developing/clients/jsonrpc-api#getbalance
		:param user:
		:return:
		"""
		addr=self.find_address_from_json(user)
		payload={
			"method":"getBalance",
			"params":[addr],
			"jsonrpc": "2.0",
			"id":0
		}

		rc=requests.post(self.api+":8899",payload,headers={"Content-Type":"application/json"}).json()
		return rc


	def toKeypair(self,txt):
		if type(txt)==str:
			if "," in txt:
				txt=txt.replace("[","").replace("]","").split(",")
				return Keypair.from_secret_key(bytes([int(x) for x in txt]))
			else:
				return Keypair.from_secret_key(base58.b58decode(txt))
		else:
			return None



	def get_keys(self):
		rc=[]
		for f in listdir(SOLANA_KEY_DIR):
			if f.endswith(".json"):
				txt=open(SOLANA_KEY_DIR+f,"r").readlines()
				keypair=self.toKeypair(txt[0])

				rc.append({"name":f.replace(".json",""),"pubkey":str(keypair.public_key.to_base58(),"utf8")})
		return rc


	def find_json_from_address(self,addr:str):
		for k in self.get_keys():
			if k["pubkey"]==addr:
				return SOLANA_KEY_DIR+k["name"]+".json"
		return addr


	def find_address_from_json(self,name:str,field="pubkey"):
		for k in self.get_keys():
			if k["name"]==name:
				return k[field]
		return None
