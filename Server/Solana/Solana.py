import json
import os
import platform
import subprocess
from datetime import datetime
from os import listdir
from time import sleep
from solana.rpc.api import Client

import base58
import requests
from solana.keypair import Keypair
from solana.rpc.commitment import Confirmed

from Tools import log

SOLANA_KEY_DIR="./Solana/Keys/"
METABOSS_DIR="./Server"

class Solana:
	def __init__(self,network="devnet"):
		self.network=network.replace("solana-","").replace("solana_","")
		self.api="https://api.mainnet-beta.solana.com" if network=="mainnet" else "https://api.devnet.solana.com"
		self.client=Client(self.api,Confirmed)


	def exec(self,command:str,param:str="",account:str="",keyfile="admin.json",data=None,sign=False):
		keyfile=keyfile +".json" if not keyfile.endswith(".json") else keyfile
		keyfile="./Keys/"+keyfile if not keyfile.startswith("./Keys") else keyfile

		os.chdir("./Solana")

		file_to_mint="./Temp/to_mint_"+str(datetime.now().timestamp())+".json"
		with open(file_to_mint, 'w') as f:
			f.writelines(json.dumps(data,indent=4, sort_keys=True))
			f.close()

		mes=None
		progname="metaboss-ubuntu-latest" if platform.system()!="Windows" else "metaboss.exe"
		if progname in os.listdir():
			cmd=progname+" "+command+" "+param+" --keypair "+keyfile+" --log-level info -r "+self.api
			if len(account)>0:cmd=cmd+" --account "+account
			cmd=cmd+" --nft-data-file "+file_to_mint+(" --sign" if sign else "")

			log(cmd)
			mes=subprocess.run(cmd,capture_output=True,timeout=10000,shell=True)
			sleep(1.0)
		else:
			log(progname+" non installé")

		if len(mes.stderr)==0: os.remove(file_to_mint)

		os.chdir("..")

		if len(mes.stderr)==0:
			rc=str(mes.stdout,"ansi").split("account: ")[1].split("\nTx")[0]
		else:
			rc="error"

		return {
			"error":str(mes.stderr,"ansi"),
			"result":rc,
			"link":"https://solscan.io/token/"+rc+"?cluster="+self.network,
			"out":str(mes.stdout,"ansi"),
			"command":cmd}



	def balance(self,user):
		"""
		https://docs.solana.com/developing/clients/jsonrpc-api#getbalance
		:param user:
		:return:
		"""
		addr=self.find_address_from_json(user,'')
		rc=self.client.get_balance(addr["pubkey"],Confirmed)
		balance=rc["result"]["value"]/1e9
		return balance


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
				if len(field)>0:
					return k[field]
				else:
					return k
		return None
