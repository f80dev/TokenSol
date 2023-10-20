import base64
import json
import random
from datetime import timedelta
from os import listdir

from flaskr.GitHubStorage import GithubStorage
from flaskr.Keys import Key
from flaskr.MegaUpload import MegaUpload
from flaskr.Network import Network
from flaskr.Polygon import Polygon
from flaskr.StoreFile import StoreFile

import requests
import yaml


from flaskr.Elrond import Elrond
from flaskr.NFT import NFT


from flaskr.Tools import log, send_mail, open_html_file, get_operation, returnError, encrypt, decrypt, is_email, now

from flaskr.dao import DAO
from flaskr.infura import Infura
from flaskr.ipfs import IPFS
from flaskr.nftstorage import NFTStorage

from flaskr.settings import IPFS_SERVER, OPERATIONS_DIR
from flaskr.storj import Storj


def get_operations() -> [dict]:
  """
  retourne l'ensemble des opérations disponibles sur le serveur
  :return:
  """
  rc=[]
  for name in listdir(OPERATIONS_DIR):
    if name.endswith(".yaml"):
      rc.append(get_operation(name))
  return rc





def open_operation(ope):
  """
  Permet de récupérer une opération
  :param ope:
  :return:
  """
  rc=None
  if ope is None:return rc
  if type(ope)==str:
    if ope.startswith("b64:"):ope=str(base64.b64decode(ope[4:]),"utf8")
    if ope.startswith("http"):
      rc=yaml.load(requests.get(ope).text,Loader=yaml.FullLoader)
    else:
      with open(OPERATIONS_DIR+ope+(".yaml" if not ope.endswith(".yaml") else ""),"r") as file:
        rc=yaml.load(file,Loader=yaml.FullLoader)
  else:
    if ope.json:
      rc=ope.json
    else:
      rc=yaml.load(ope.data,Loader=yaml.FullLoader)

  #Vérification de la conformité
  for field in ["title","data"]:
    if not field in rc:
      log("Le champs "+field+" est obligatoire dans une opération")
      rc=None
      break

  return rc


def get_nfts_from_src(srcs,collections=None,with_attributes=False) -> list[NFT]:
  """
  Récupération des NFTS depuis différentes sources (#getnftfromsrc)
  :param srcs:
  :param collections: filtre sur les collections à utiliser
  :return:
  """
  if type(collections)==str:collections=[collections]
  nfts=[]

  for src in srcs:
    if src["active"]:
      log("Récupération des nfts depuis "+str(src))

      if not "filter" in src:src["filter"]={"owner":None,"collections":[]}
      if not "collections" in src["filter"]:src["filter"]["collections"]=[];
      if not "limit" in src: src["limit"]=10000
      owner=src["owner"] if "owner" in src else None

      _network=get_network_instance(src["network"] if "network" in src else src["connexion"])
      if "collection" in src:
        nfts=nfts+_network.get_nfts_from_collections(src["collection"])
      else:
        nfts=nfts+_network.get_nfts(owner)

      src["ntokens"]=len(nfts)

  return nfts


def extract_keys_from_operation(ope):
  if ope is None or not "keys" in ope: return []
  rc=[]
  for k in ope["keys"]:
    private_key=decrypt(ope["keys"][k])
    rc.append(Key(name=k,secret_key=private_key))
  return rc


def airdrop(address:str,token:dict,collection:str,_miner:Key,amount:float,histo:DAO,limit:float,network:str,wallet_limit:float=0,comment="airdrop",delay_between_airdrop=30) -> dict :
  rc={"address":address}
  if histo:
    total=0
    for h in histo.get_histos(addr=address,start=now()-24*1000):
      if h["command"]=="refund": total=total+int(h["params"][0])
    if total>=limit:
      return {"error":"Plafond de versement atteint pour la journée","status":"error"}

  _network=get_network_instance(network)

  #Vérifier qu'il n'y a pas eu une transaction dans l'heure précédente
  transactions=_network.get_transactions(address,limit=20,size=10,profondeur=0,profondeur_max=-1)
  for t in transactions:
    if t["method"]=="ESDTTransfer" and t["to"]==address and t['token']==token["id"]:
      #Pas d'airdrop avec moins de 30 minutes d'interval
      delay=now()-t["ts"]
      if delay<delay_between_airdrop*60: return {"error":"airdrop trop récent","status":"error"}

  if wallet_limit>0:
    balances=_network.get_balances(address)
    if token in balances and balances[token]>=wallet_limit:
      return {"error":"Limite du wallet atteinte","status":"error"}

  if token:
    if type(token)==dict and "identifier" in token:token=token["identifier"]
    tx_esdt=_network.transfer_money(token,_miner,address,float(amount),data=comment)
    if tx_esdt["status"]!="success":
      return {"error":tx_esdt["error"],"status":"error"}
  else:
    _nfts=[]
    for nft in _network.get_nfts_from_collections([collection],with_attr=False,limit=100):
      if _miner.address in nft.balances.keys(): _nfts.append(nft)

    if len(_nfts)<amount:
      log("Pas assez de NFTs disponible dans la collection")
      rc["status"]="error"
      return rc

    for i in range(amount):
      _nft=_nfts[random.randint(0,len(_nfts)-1)]
      tx_esdt=_network.transfer(_nft.address,_miner,address,1)
      _nfts.remove(_nft)

  if histo: histo.add_histo(command="refund",addr=address,transaction_id=tx_esdt["hash"],network=_network.network,comment="Rechargement",params=[int(amount)])
  rc["transaction_esdt"]=tx_esdt
  rc["status"]="success"
  return rc


def get_network_instance(network:str):
  if type(network)==Network: return network
  _network=None
  if not "-" in network: network=network+"-mainnet"
  if "elrond" in network:_network=Elrond(network)
  # if "solana" in network:_network=Solana(network)
  if "polygon" in network:_network=Polygon(network)
  if network.startswith("db-"): _network= DAO(network=network)
  if network.startswith("file"): _network=StoreFile(network=network,domain_server="")

  #log("Création d'une instance de "+network)

  return _network




def get_network_from_address(addr:str):
  """
  retourne le réseau d'une addresse
  :param addr:
  :return:
  """
  if addr.lower()=="egld": return "elrond"
  if addr.startswith("erd"):return "elrond"
  if addr.startswith("db_"):return "db"
  if addr.startswith("file_"):return "file"
  if addr.startswith("0x"):return "polygon"
  if len(addr.split("-"))==3: return "elrond"
  log("l'adresse "+addr+" ne correspond a aucune blockchaine")
  return None


def get_storage_instance(platform="nftstorage",domain_server="http://localhost:4242/"):
  name=platform.lower().split("-")[0]
  if name.startswith("storj"): return Storj(network=platform,domain_server=domain_server)
  if name.startswith("file"): return StoreFile(network=platform,domain_server=domain_server)
  if name.startswith("github"): return GithubStorage(platform=domain_server)
  if name.startswith("dao") or name=="db": return DAO(network=platform,domain_server=domain_server)
  if name.startswith("infura"):return Infura()
  if name.startswith("ipfs"):return IPFS(IPFS_SERVER)
  if name.startswith("megaupload"):return MegaUpload(directory=domain_server)
  return NFTStorage()


def create_account(email,network,domain_appli,histo,mail_new_wallet,mail_existing_wallet,dictionnary={},send_real_email=True,subject="") -> Key:
  """
  Créé un compte en multiréseau
  :param email:
  :param network:
  :param domain_appli:
  :param histo:
  :param mail_new_wallet: {{network}} est remplacé par le nom du réseau
  :param mail_existing_wallet:
  :param dictionnary:
  :param send_real_email:
  :param subject:
  :return:
  """
  _network=get_network_instance(network)
  if _network.is_blockchain() and not is_email(email): return Key(address=email)
  if not mail_new_wallet.endswith(".html"):mail_new_wallet=mail_new_wallet+".html"
  mail_new_wallet=mail_new_wallet.replace("{{network}}",_network.network_name)
  key=_network.create_account(email=email,
                              histo=histo,
                              subject=subject,
                              domain_appli=domain_appli,
                              mail_new_wallet=mail_new_wallet,
                              mail_existing_wallet=mail_existing_wallet,
                              send_real_email=send_real_email,
                              dictionnary=dictionnary
                              )
  #TODO: a voir si peut être supprimé
  return key



def transfer(addr:str,
             from_network_miner:Key,
             from_network:str,
             target_network_miner:Key=None,
             target_network_owner:str=None,
             target_network:str=None,
             collection:dict=None,
             quantity=1,
             metadata_storage_platform="nftstorage"):
  """
  Transfer un NFT d'un réseau à un autre
  :param addr:
  :param miner:
  :param new_owner:
  :param target_network:
  :param metadata_storage_platform:
  :return:
  """
  if target_network is None:target_network=from_network
  _target_network=get_network_instance(target_network)

  if target_network_owner is None:target_network_owner=target_network_miner.address
  if target_network_miner is None:
    if from_network==target_network:
      target_network_miner=from_network_miner
    else:
      raise RuntimeError("Il manque le miner du réseau cible")

  if get_network_from_address(addr) not in from_network: return returnError("!Le NFT ne fait pas partie de la blockchain d'origine")
  #if get_network_from_address(target_network_owner) not in target_network: return returnError("!Le nouveau propriétaire ne fait pas partie de la blockchain finale")
  if get_network_from_address(from_network_miner.address) not in from_network: return returnError("!Le mineur ne fait pas partie de la blockchain finale")

  log("Tranfert de "+addr+" du réseau "+from_network+" vers le réseau "+target_network+" pour le compte de "+target_network_owner)
  nft:NFT=get_network_instance(from_network).get_nft(addr,attr=True)

  if from_network!=target_network:
    _storage=get_storage_instance(metadata_storage_platform)

    rc=_target_network.mint(target_network_miner,nft.name,nft.description,collection,nft.attributes,_storage,nft.files,
                    quantity,nft.royalties,nft.visual,nft.tags,nft.creators)

    if rc["error"]=="":
      nft.address=rc["result"]["mint"]
      get_network_instance(from_network).burn(addr,from_network_miner,quantity=quantity)
    return rc
  else:
    rc=_target_network.transfer(addr,from_network_miner,target_network_owner,quantity=quantity)
    return {"error":"probleme technique au transfert" if not rc else "","result":{"mint":nft.address}}





def mint(nft:NFT,network:Network,
         offchaindata_platform:str="IPFS",
         domain_server=None,price=0) -> dict:
  """
  minage du NFT
  :param nft:
  :param miner:
  :param owner:
  :param network:
  :param offchaindata_platform:
  :param wallet_appli:
  :return:
  """

  storage=get_storage_instance(offchaindata_platform)
  if not nft.address is None and len(nft.address)>0: return returnError("!Ce NFT est déjà miner")

  #if len(miner.address)==0: return returnError("!L'address du mineur est indispensable")
  # if len(miner.secret_key)==0:
  #   for k in network.get_keys():
  #     if k.address==miner.address: miner=k
  # if len(miner.secret_key)==0: return returnError("!La clé privée du mineur est indispensable")
  # if len(miner.address)>0 and not get_network_from_address(miner.address) in network.network_name: return returnError("!L'address du mineur ne correspond pas au réseau cible")


  #if collection_id=="": returnError("!La collection est indispensable")

  #if not _ope is None: dao.add_histo(_ope["id"],"new_account",account,"","",_ope["network"],"Création d'un compte pour "+owner,owner)

  t=network.mint(nft,storage=storage,price=price)
  return t


# def execute(t:dict,network:Network):
#   """
#     Execute une transaction
#   """
#
#   rc=dict()
#
#   # if "solana" in network.network.lower():
#   #   #voir https://metaboss.rs/mint.html
#   #   #(request.args.get("sign","True")=="True" or request.args.get("sign","all")=="all")
#   #   if request.args.get("sign_all","False")=="True" and "result" in rc and "mint" in rc["result"]:
#   #     signers=[x["address"] for x in nft.creators]
#   #     #signers.remove(solana.find_address_from_json(keyfile))
#   #     network.sign(rc["result"]["mint"],signers)
#
#
#
#   # if miner.address!=owner:
#   #   tx_transfer=network.transfer(nft.address,miner,owner,nft.supply)
#   #   if not tx_transfer or len(tx_transfer["error"])>0:
#   #     rc["error"]=tx_transfer["error"]
#   #     return rc
#   #   nft.owner=owner
#
#
#   # Transfert des NFTs vers la base de données
#   rc["cost"]=network.get_account(miner.address).amount-old_amount if len(miner.address)>0 else 0
#   rc["link"]=network.getExplorer(nft.address,"nfts")
#
#   if type(network)==StoreFile:
#     if encrypt_nft:
#       rc["out"]=encrypt(rc["out"],format="txt")
#
#
#   # if "jsonfiles" in network.lower():
#   #   filename=_data["name"]+"_"+_data["symbol"]+"_"+_data["collection"]+".json"
#   #   with open(TEMP_DIR+filename,"w") as f:
#   #     json.dump(_data,f,indent=4)
#   #   rc={
#   #     "error":"",
#   #     "uri":_data["uri"],
#   #     "result":{"transaction":"","mint":filename},
#   #     "balance":0,
#   #     "link_mint":"",
#   #     "link_transaction":"",
#   #     "out":"",
#   #     "command":"file"
#   #   }
#
#   return rc




def activity_report_sender(config,event:str="CR d'activité",sender="support@nfluent.io"):
  """
  Envoi un mail sur l'activité du serveur
  :param activity_report_dest:
  :param domain_appli:
  :param event:
  :return:
  """
  domain_server=config["DOMAIN_SERVER"]
  domain_appli=config["DOMAIN_APPLI"]
  dest=config["ACTIVITY_REPORT"]
  log(event)

  temp_config=dict()
  for k in config.keys():
    if not k.startswith("JWT") and not k=="socket" and not type(config[k])==timedelta: temp_config[k]=config[k]

  mail=open_html_file("mail_activity_report",{
    "DOMAIN_SERVER":domain_server,
    "DOMAIN_APPLI":domain_appli,
    "event":event,
    "config":json.dumps(temp_config,allow_nan=False,sort_keys=True,indent=4,ensure_ascii=False).replace("\n","<br>")
  })
  if mail:
    return send_mail(mail,_from=sender,_to=dest,subject="ACTIVITY REPORT de "+domain_server+" - "+event[:60])

  return False




