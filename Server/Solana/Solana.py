import base64
import json
import os
import platform
import subprocess
from datetime import datetime
from os import listdir
from os.path import exists
from time import sleep

import requests
from solana.publickey import PublicKey
from solana.rpc.api import Client

import base58
from solana.keypair import Keypair
from solana.rpc.commitment import Confirmed
from solana.rpc.types import TokenAccountOpts
from spl.token.constants import TOKEN_PROGRAM_ID

from Tools import log

SOLANA_KEY_DIR="./Solana/Keys/"
METABOSS_DIR="./Solana/"

class Solana:
  def __init__(self,network="devnet"):
    self.network=network.replace("solana-","").replace("solana_","")
    self.api="https://api.mainnet-beta.solana.com" if network=="mainnet" else "https://api.devnet.solana.com"
    self.client=Client(self.api,Confirmed)


  def get_token(self,addr:str,network="devnet"):
    token={}
    rc=self.client.get_account_info(PublicKey(addr),Confirmed,encoding="jsonParsed")
    token["accountInfo"]=rc["result"]["value"]["data"]
    rc=self.scan(addr,network)
    token["metadataOnchain"]=rc
    return token



  def exec(self,command:str,param:str="",account:str="",keyfile="admin.json",data=None,sign=False,delay=1.0,owner=""):
    if len(owner)>0:owner=self.find_address_from_json(owner)

    if "Solana" in os.listdir(): os.chdir("./Solana")
    keyfile=keyfile +".json" if not keyfile.endswith(".json") else keyfile
    if not keyfile in os.listdir("./Keys/"):
      log("Clé introuvable")
      return {"error":keyfile+" introuvable"}

    keyfile="./Keys/"+keyfile if not keyfile.startswith("./Keys") else keyfile

    if data:
      file_to_mint="./Temp/to_mint_"+str(datetime.now().timestamp())+".json"
      with open(file_to_mint, 'w') as f:
        f.writelines(json.dumps(data,indent=4, sort_keys=True))
        f.close()

    mes=None
    progname="./metaboss-ubuntu-latest" if platform.system()!="Windows" else "metaboss.exe"
    encoder="ANSI" if platform.system()=="Windows" else "utf8"

    if progname.replace("./","") in os.listdir():
      cmd=progname+" "+command+" "+param+" --keypair "+keyfile+" -r "+self.api
      if len(account)>0:cmd=cmd+" --account "+account
      if len(owner)>0:cmd=cmd+" --receiver "+owner
      if data: cmd=cmd+" --nft-data-file "+file_to_mint+(" --sign" if sign else "")

      log(cmd)
      mes=subprocess.run(cmd,capture_output=True,timeout=10000,shell=True)
      sleep(delay)
    else:
      log(progname+" non installé")

    if len(mes.stderr)==0 and data:
      if exists(file_to_mint):os.remove(file_to_mint)

    if progname.replace("./","") in os.listdir():
      os.chdir("..")

    if len(mes.stderr)==0:
      rc=dict()
      for line in str(mes.stdout,encoder).split("\n"):
        if line.startswith("Tx id:"): rc["transaction"]=line.split(": ")[1]
        if line.startswith("Mint account: "):rc["mint"]=line.split(": ")[1]

      log(str(mes.stdout,encoder))
    else:
      rc="error"


    return {
      "error":str(mes.stderr,encoder),
      "result":rc,
      "link_mint":("https://solscan.io/token/"+rc["mint"]+"?cluster="+self.network) if "mint" in rc else "",
      "link_transaction":("https://solscan.io/tx/"+rc["transaction"]+"?cluster="+self.network) if "transaction" in rc else "",
      "out":str(mes.stdout,encoder),
      "command":cmd
    }


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



  def get_keys(self,dir=SOLANA_KEY_DIR):
    rc=[]
    for f in listdir(dir):
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


  def find_address_from_json(self,name:str,field="pubkey",dir=SOLANA_KEY_DIR):
    if len(name)>40:return name
    for k in self.get_keys(dir=dir):
      if k["name"]==name:
        if len(field)>0:
          return k[field]
        else:
          return k
    return None

  #http://127.0.0.1:4242/api/nfts/
  def get_nfts(self, name):
    pubkey=self.find_address_from_json(name)
    token_account_opts=TokenAccountOpts(mint=None,program_id=TOKEN_PROGRAM_ID)
    rc=self.client.get_token_accounts_by_owner(PublicKey(pubkey),token_account_opts,Confirmed)
    # for item in rc["result"]["value"]:
    # 	item["content"]=base64.b64decode(item["account"]["data"][0])
    return rc["result"]["value"]

  def scan(self,addr,network="devnet"):
    url="https://api-devnet.solscan.io" if network=="devnet" else "https://api.solscan.io"
    url=url+"/account?address="+addr
    rc=requests.get(url,headers={
      "Content-Type":"application/json; charset=UTF-8",
      "User-Agent":"Mozilla/5.0 (iPad; U; CPU OS 3_2_1 like Mac OS X; en-us) AppleWebKit/531.21.10 (KHTML, like Gecko) Mobile/7B405"
    })
    return rc.json()["data"]

  def get_token_by_miner(self, account):
    """
    https://docs.solana.com/developing/clients/jsonrpc-api#gettokenaccountsbydelegate
    :param account:
    :return:
    """
    rc=self.client.get_token_accounts_by_delegate(PublicKey(account),{"programId":PublicKey(TOKEN_PROGRAM_ID)},Confirmed)
    return rc

