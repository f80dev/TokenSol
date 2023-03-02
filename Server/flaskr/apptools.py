import base64
import json
from os import listdir

from flaskr import GitHubStorage
from flaskr.Keys import Key
from flaskr.Network import Network
from flaskr.Polygon import Polygon
from flaskr.StoreFile import StoreFile

import requests
import yaml
from flask import request

from flaskr.Elrond import Elrond
from flaskr.NFT import NFT
from flaskr.Solana import Solana

from flaskr.Tools import log, send_mail, open_html_file, get_operation, returnError, encrypt, decrypt

from flaskr.dao import DAO
from flaskr.infura import Infura
from flaskr.ipfs import IPFS
from flaskr.nftstorage import NFTStorage

from flaskr.settings import IPFS_SERVER, OPERATIONS_DIR


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

      _network=get_network_instance(src["network"])
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

def get_network_instance(network:str):
  _network=None
  if "elrond" in network:_network=Elrond(network)
  if "solana" in network:_network=Solana(network)
  if "polygon" in network:_network=Polygon(network)
  if network.startswith("db-"): _network= DAO(network=network)
  if network.startswith("file"): _network=StoreFile(network=network,domain_server="")

  log("Création d'une instance de "+network)

  return _network




def get_network_from_address(addr:str):
  """
  retourne le réseau d'une addresse
  :param addr:
  :return:
  """
  if addr.startswith("erd"):return "elrond"
  if addr.startswith("db_"):return "db"
  if addr.startswith("file_"):return "file"
  if addr.startswith("0x"):return "polygon"
  if len(addr.split("-"))==3: return "elrond"
  log("l'adresse "+addr+" ne correspond a aucune blockchaine")
  return None


def get_storage_instance(platform="nftstorage",domain_server="http://localhost:4242/"):
  name=platform.lower().split("-")[0]
  if name=="file": return StoreFile(network=platform,domain_server=domain_server)
  if name=="github": return GitHubStorage(platform)
  if name=="dao" or name=="db": return DAO(network=platform,domain_server=domain_server)
  if name=="infura":return Infura()
  if name=="ipfs":return IPFS(IPFS_SERVER)
  return NFTStorage()


def create_account(email,network,domain_appli,dao,mail_new_wallet,mail_existing_wallet,nft_name="",send_real_email=True) -> Key:
  _network=get_network_instance(network)
  key=_network.create_account(email=email,histo=dao,
                                                          subject="Votre NFT '"+nft_name+"' est disponible",
                                                          domain_appli=domain_appli,
                                                          mail_new_wallet=mail_new_wallet,
                                                          mail_existing_wallet=mail_existing_wallet,send_real_email=send_real_email)
  return key



def transfer(addr:str,
             from_network_miner:Key,
             from_network:str,
             target_network_miner:Key=None,
             target_network_owner:str=None,
             target_network:str=None,collection:str=None,
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
  if get_network_from_address(target_network_owner) not in target_network: return returnError("!Le nouveau propriétaire ne fait pas partie de la blockchain finale")
  if get_network_from_address(from_network_miner.address) not in from_network: return returnError("!Le mineur ne fait pas partie de la blockchain finale")

  log("Tranfert de "+addr+" du réseau "+from_network+" vers le réseau "+target_network+" pour le compte de "+target_network_owner)
  nft:NFT=get_network_instance(from_network).get_nft(addr,attr=True)
  # if (nft.address.startswith(DB_PREFIX_ID) or nft.address.startswith(FILE_PREFIX_ID)) and nft.marketplace["quantity"]==0:
  #   returnError("!Ce NFT n'est plus disponible")


  if from_network!=target_network:
    _storage=get_storage_instance(metadata_storage_platform)
    if "elrond" in target_network and collection=="": collection={"id":nft.collection["id"]}

    rc=_target_network.mint(target_network_miner,nft.name,nft.description,collection,nft.attributes,_storage,nft.files,
                    nft.marketplace["quantity"],nft.royalties,nft.visual,nft.tags,nft.creators)
    nft.address=rc["result"]["mint"]
    get_network_instance(from_network).burn(addr,from_network_miner,1)
    return rc
  else:
    rc=_target_network.transfer(addr,from_network_miner,target_network_owner)
    return {"error":"probleme technique au transfert" if not rc else "","result":{"mint":nft.address}}





def mint(nft:NFT,miner:Key,owner,network:Network,
         offchaindata_platform:str="IPFS",
         domain_server=None,
         operation=None,
         dao=None,encrypt_nft=False,price=0,symbol="NFluentToken"):
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
  if len(miner.secret_key)==0:
    for k in network.get_keys():
      if k.address==miner.address: miner=k
  if len(miner.secret_key)==0: return returnError("!La clé privée du mineur est indispensable")
  if not get_network_from_address(miner.address) in network.network_name: return returnError("!L'address du mineur ne correspond pas au réseau cible")

  collection=nft.collection if nft.collection else {}
  #if collection_id=="": returnError("!La collection est indispensable")

  nft.miner=miner.address
  #if not _ope is None: dao.add_histo(_ope["id"],"new_account",account,"","",_ope["network"],"Création d'un compte pour "+owner,owner)

  old_amount=network.get_account(miner.address).amount
  rc=network.mint(miner,
                     title=nft.name,
                     description=nft.description,
                     tags=nft.tags,
                     collection=collection,
                     properties=nft.attributes,
                     files=nft.files,
                     storage=storage,
                     quantity=nft.marketplace["quantity"],
                     royalties=nft.royalties,  #On ne prend les royalties que pour le premier créator
                     visual=nft.visual,
                     creators=nft.creators,
                     domain_server=domain_server,price=price,symbol=symbol)

  if rc is None: return returnError("!"+rc["error"])

  nft.address=rc["result"]["mint"] if "result" in rc else ""
  if "elrond" in network.network:
    collection_id,nonce = network.extract_from_tokenid(nft.address)
    if nonce is None:
      rc={"error":"Mint error: "+rc["error"],"hash":rc["hash"]}
    else:
      if miner.address!=owner:
        tx_transfer=network.transfer(nft.address,miner,owner)
        if not tx_transfer or len(tx_transfer["error"])>0:
          rc["error"]=tx_transfer["error"]
          return rc

  if "solana" in network.network.lower():
    #voir https://metaboss.rs/mint.html
    #(request.args.get("sign","True")=="True" or request.args.get("sign","all")=="all")
    if request.args.get("sign_all","False")=="True" and "result" in rc and "mint" in rc["result"]:
      signers=[x["address"] for x in nft.creators]
      #signers.remove(solana.find_address_from_json(keyfile))
      network.sign(rc["result"]["mint"],signers)



  # Transfert des NFTs vers la base de données

  rc["cost"]=network.get_account(miner.address).amount-old_amount
  rc["link"]=network.getExplorer(nft.address,"nfts")

  if type(network)==StoreFile:
    if encrypt_nft:
      rc["out"]=encrypt(rc["out"],format="txt")


  # if "jsonfiles" in network.lower():
  #   filename=_data["name"]+"_"+_data["symbol"]+"_"+_data["collection"]+".json"
  #   with open(TEMP_DIR+filename,"w") as f:
  #     json.dump(_data,f,indent=4)
  #   rc={
  #     "error":"",
  #     "uri":_data["uri"],
  #     "result":{"transaction":"","mint":filename},
  #     "balance":0,
  #     "link_mint":"",
  #     "link_transaction":"",
  #     "out":"",
  #     "command":"file"
  #   }

  if ("result" in rc) and ("transaction" in rc["result"]) and (network.network!="file") and not dao is None:
    dao.add_histo(request.args.get("ope",""),"mint",miner.address,collection["id"],rc["result"]["transaction"],network.network,"Minage")

  return rc




def activity_report_sender(config,event:str="CR d'activité"):
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
  if not "localhost" in domain_server and not "127.0.0.1" in domain_server:
    mail=open_html_file(config["STATIC_FOLDER"]+"mail_activity_report",{
      "DOMAIN_SERVER":domain_server,
      "DOMAIN_APPLI":domain_appli,
      "event":event
    })
    send_mail(mail,_to=dest,subject="ACTIVITY REPORT de "+domain_server+" - "+event[:60])



