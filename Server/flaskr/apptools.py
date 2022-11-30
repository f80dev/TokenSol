import base64
import json
from os import listdir
from random import random

from flaskr.Polygon import Polygon
from flaskr.StoreFile import StoreFile
from flaskr.TokenForge import upload_on_platform

import requests
import yaml
from flask import request
from flaskr.Elrond import Elrond
from flaskr.NFT import NFT
from flaskr.Solana import Solana

from flaskr.Tools import log, now, is_email, send_mail, open_html_file,get_operation

from flaskr.dao import DAO
from flaskr.ipfs import IPFS

from flaskr.settings import IPFS_SERVER


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


def get_nfts_from_src(srcs,collections=None,with_attributes=False,domain_server=None) -> list[NFT]:
  """
  Récupération des NFTS depuis différentes sources (#getnftfromsrc)
  :param srcs:
  :param collections: filtre sur les collections à utiliser
  :return:
  """
  nfts=[]
  for src in srcs:
    if src["active"]:
      log("Récupération des nfts depuis "+str(src))

      if not "filter" in src:src["filter"]={}
      if not "limit" in src["filter"]: src["filter"]["limit"]=10000

      if src["type"] in ["database","db"]:
        try:
          if not "connexion" in src or not "dbname" in src:
            raise RuntimeError("Champs dbname ou connexion manquant dans la source")

          _dao_temp=DAO(src["connexion"],src["dbname"])
          if collections and len(collections)>0:
            for collection in collections:
              if _dao_temp.isConnected():
                l_nfts=list(_dao_temp.nfts_from_collection(collection))
                nfts=nfts+l_nfts[:src["filter"]["limit"]]
                src["ntokens"]=len(l_nfts)
              else:
                log("Impossible de se connecter a la base de donnée pour récupérer les NFT")
          else:
            #Si le filtre sur les collections n'a pas été précisé ou si vide, on prend tous les NFTs des sources
            if _dao_temp.isConnected():
              l_nfts=list(_dao_temp.nfts_from_collection(None))
              nfts=nfts+l_nfts[:src["filter"]["limit"]]

          src["ntokens"]=len(l_nfts)
        except Exception as inst:
          log("Probleme de lecture de "+src["connexion"]+" "+str(inst.args))


      if src["type"]=="file":
        l_nfts=[]
        if not "connexion" in src or len(src["connexion"])==0:
          for nft in src["nfts"]:
            l_nfts.append(NFT(object=nft))
        else:
          if src["connexion"].startswith("http"):
            r=requests.get(src["connexion"])
            if src["connexion"].endswith(".json"):l_nfts=l_nfts+json.loads(r.text)
            if src["connexion"].endswith(".yaml"):l_nfts=l_nfts+yaml.load(r.text,Loader=yaml.FullLoader)
          else:
            sf=StoreFile(src["connexion"])

        #On retrouve l'intégralité des collections en utilisant une technique de cache
        collections=dict()
        for nft in l_nfts:
          if not nft.collection["id"] in collections:
            collections[nft.collection["id"]]=Elrond(nft.network).get_collection(nft.collection["id"]) if "elrond" in nft.network else nft.collection
          nft.collection=collections[nft.collection["id"]]
        nfts=nfts+l_nfts


      if src["type"]=="network":
        if src["connexion"].startswith("solana"):
          l_nfts=Solana(src['connexion']).get_nfts(src["owner"],limit=src["filter"]["limit"])
          nfts=nfts+l_nfts
          src["ntokens"]=len(l_nfts)

        if src["connexion"].startswith("polygon"):
          l_nfts=Polygon(src['connexion']).get_nfts(src["owner"],limit=src["filter"]["limit"])
          nfts=nfts+l_nfts
          src["ntokens"]=len(l_nfts)

        if src["connexion"].startswith("elrond"):
          elrond=Elrond(src['connexion'])
          if src["owner"]:
            nfts=elrond.get_nfts(src["owner"],limit=src["filter"]["limit"],with_attr=with_attributes)
          else:
            log("Récupération depuis les collections "+" ".join(src["collections"]))
            nfts=elrond.get_nfts_from_collections(src["collections"],with_attr=with_attributes)

          nfts=elrond.complete_collection(nfts)

          src["ntokens"]=len(nfts)


      #TODO a retravailler pour permettre de refrabriquer la collection à partir du fichier de config
      # if src["type"]=="config":
      #   config=configs(src["connexion"],format="dict")
      #   for layer in config["layers"]: layers(layer)
      #
      #   files=get_collection(
      #     size=(config["width"],config["height"]),
      #     format="list",
      #     seed=src["seed"] if "seed" in src else 1,
      #     limit=src["limit"] if "limit" in src else 10,
      #     data={
      #       "title":"MonTitre",
      #       "symbol":"token__idx__",
      #       "description":"madescription",
      #       "collection":"macollection",
      #       "properties":"propriete=valeur",
      #       files:"http://monfichier"
      #     }
      #   )
      #   for file in files:
      #     id=file[file.rindex("/")+1:]
      #     nfts.append({
      #       "uri":file,
      #       "image":domain_server+"/api/images/"+id,
      #       "id":id,
      #       "creators":[{"address":x} for x in src["creators"]]
      #     })

  return nfts





def get_network_instance(network:str):
  if "elrond" in network:return Elrond(network)
  if "solana" in network:return Solana(network)
  if "polygon" in network:return Polygon(network)
  return None



def async_mint(dao,nbr_items=3,filter=""):
  message=""
  if not dao.isConnected():
    message="Impossible de se connecter à la base"

  if message=="":
    for ask in dao.get_nfts_to_mint(int(nbr_items),filter):
      log("Traitement de la demande "+str(ask["_id"]))
      dao.edit_pool(ask["_id"],now(),"traitement en cours")
      nfts=get_nfts_from_src(ask["sources"],ask["filter"],False)
      _ope=get_operation(ask["operation"])

      nft_to_mint=None
      if "elrond" in ask["network"]:
        elrond=Elrond(ask["network"])
        _miner=elrond.toAccount(ask["miner"])

        if len(nfts)>0:
          log("Tirage au sort d'un NFT parmis la liste de "+str(len(nfts)))
          for i in range(200):
            nft_to_mint=nfts[int(random()*len(nfts))]

            if nft_to_mint.owner=="":
              if nft_to_mint.collection is None:
                nft_to_mint.collection=get_network_instance(ask["network"]).get_collection(ask["collection_to_mint"])

              if elrond.canMint(nft_to_mint,ask["dest"]): break
            else:
              if not _miner is None and nft_to_mint.owner==_miner.address.bech32(): break
        else:
          log("Aucun NFT à miner")

      if not nft_to_mint is None:
        log("Minage de "+nft_to_mint.name+" en cours")
        if _miner is None:
          log("Le miner est fixé sur le propriétaire de la collection "+nft_to_mint.collection["id"])
          if "elrond" in ask["network"]:
            _miner=elrond.toAccount(nft_to_mint.collection["owner"])
            if _miner.secret_key is None:
              message="On ne dispose pas de la clé privée du propriétaire de la collection "+nft_to_mint.collection["id"]+", donc pas de minage possible"
              #activity_report_sender(message)

        if message=="":
          log("Ajout de l'attribut lazymint pour ne pas risquer de re-minté")
          nft_to_mint.attributes.append({"trait_type":"lazymint","value":nft_to_mint.address})
          rc=mint(nft_to_mint,
                  _miner.address.bech32(),
                  ask["dest"],
                  ask["network"],
                  mail_new_wallet=_ope["new_account"]["mail"],mail_existing_wallet=_ope["transfer"]["mail"]
                  )
          if not rc or rc["error"]!="":
            log("Problème de minage voir "+rc["hash"])
            message="Error"+rc["error"]+" voir "+elrond.getExplorer(rc["hash"])
          else:
            message="Ok. Transaction="+rc["hash"]

        log("Mise a jour des données de la pool de minage avec message:"+message)
        dao.edit_pool(ask["_id"],now(),message)

      else:
        message="Aucun NFT disponible pour le minage"
        log(message)
        dao.edit_pool(ask["_id"],now(),message)


def mint(nft:NFT,miner,owner,network,offchaindata_platform="IPFS",storagefile="",mail_new_wallet="",mail_existing_wallet="",
         application_root=None,domain_appli=None,dao=None):
  """
  minage du NFT
  :param nft:
  :param miner:
  :param owner:
  :param network:
  :param offchaindata_platform:
  :param storagefile:
  :param wallet_appli:
  :return:
  """
  if len(mail_existing_wallet)==0:mail_existing_wallet="mail_existing_account"
  if len(mail_new_wallet)==0:mail_new_wallet="mail_new_account"

  rc= {"error":"Problème technique"}
  account=None
  collection_id=nft.collection["id"] if nft.collection else ""

  if is_email(owner):
    email=owner
    if "elrond" in network:
      elrond=Elrond(network)
      _account,pem,words,qrcode=elrond.create_account(email=email,histo=dao,
                                                      subject="Votre NFT '"+nft.name+"' est disponible",
                                                      domain_appli=domain_appli,
                                                      mail_new_wallet=mail_new_wallet,mail_existing_wallet=mail_existing_wallet)
      account=_account.address.bech32()
      log("Notification de "+owner+" que son compte "+elrond.getExplorer(account,"account")+" est disponible")

    if "solana" in network:
      solana=Solana(network)
      words,pubkey,privkey,list_int=solana.create_account(domain_appli=domain_appli,subject="Votre NFT '"+nft.name+"' est disponible")
      account=pubkey

    if "polygon" in network:
      words,pubkey,privkey,list_int=Polygon(network).create_account(domain_appli=domain_appli,histo=dao,
                                                                    subject="Votre NFT '"+nft.name+"' est disponible")
      account=pubkey

  if account is None:
    if "elrond" in network:
      elrond=Elrond(network)
      account=elrond.toAccount(owner)
      if account is None:
        log("Impossible de reconnaitre "+owner)
      else:
        account=account.address.bech32()

    # if not _ope is None:
    #   dao.add_histo(_ope["id"],"new_account",account,"","",_ope["network"],"Création d'un compte pour "+owner,owner)

  if len(miner)==0:miner=owner


  if "polygon" in network:
    rc=Polygon(network).mint(
      miner,
      title=nft.name,
      description=nft.description,
      tags=nft.tags,
      collection=None,
      properties=nft.attributes,
      files=nft.files,
      ipfs=IPFS(IPFS_SERVER),
      quantity=nft.marketplace["quantity"],
      royalties=nft.royalties,  #On ne prend les royalties que pour le premier créator
      visual=nft.visual,
      creators=nft.creators
    )


  if "elrond" in network.lower() and not account is None:
    elrond=Elrond(network)
    old_amount=elrond.get_account(miner)["amount"]

    if nft.address.startswith("file_") or nft.address.startswith("db_") or len(nft.address)==0:
      nonce,rc=elrond.mint(miner,
                              title=nft.name,
                              description=nft.description,
                              tags=nft.tags,
                              collection=collection_id,
                              properties=nft.attributes,
                              files=nft.files,
                              ipfs=IPFS(IPFS_SERVER),
                              quantity=nft.marketplace["quantity"],
                              royalties=nft.royalties,  #On ne prend les royalties que pour le premier créator
                              visual=nft.visual
                              )
    else:
      rc={"error":"NFT deja miné","hash":"","result":{"mint":nft.address}}
      collection_id,nonce = elrond.extract_from_tokenid(nft.address)

    if nonce is None:
      rc={"error":"Mint error: "+rc["error"],"hash":rc["hash"]}
    else:
      infos=elrond.get_account(miner)
      token_id=collection_id+"-"+nonce

      if elrond.toAccount(miner).address.bech32()!=account:
        rc=elrond.transfer(collection_id,nonce,miner,account)
        if not rc or len(rc["error"])>0:
          return rc

      solde=elrond.get_account(miner)["amount"]-old_amount
      rc={"command":"ESDTCreate",
          "error":"",
          "link":elrond.getExplorer(token_id,"nfts"),
          "uri":"",
          "out":"",
          "hash":rc["hash"],
          "cost":solde,
          "result":{
            "transaction":token_id,
            "mint":token_id
          },
          "unity":"EGLD",
          "link_transaction":elrond.getExplorer(token_id,"nfts"),
          "link_mint":elrond.getExplorer(token_id,"nfts"),
          "balance":int(infos["balance"])/1e18
          }

  if "solana" in network.lower():
    solana=Solana(network)
    offchain_uri=upload_on_platform(solana.prepare_offchain_data(nft.attributes),offchaindata_platform,
                                    id=request.args.get("filename_for_metadata",None),
                                    options={"repository":request.args.get("repository","calviontherock")},
                                    )["url"]
    #voir https://metaboss.rs/mint.html
    #(request.args.get("sign","True")=="True" or request.args.get("sign","all")=="all")
    rc=solana.mint(nft,miner=miner,sign=False,owner=request.args.get("owner",""))

    if request.args.get("sign_all","False")=="True" and "result" in rc and "mint" in rc["result"]:
      signers=[x["address"] for x in nft.creators]
      #signers.remove(solana.find_address_from_json(keyfile))
      solana.sign(rc["result"]["mint"],signers)

  # Transfert des NFTs vers la base de données
  if "database" in network.lower() or "db-" in network.lower():
    db_loc=request.args.get("db_loc","")
    if len(db_loc)==0: db_loc=network.split("-")[1]
    db_name=request.args.get("db_name","")
    if len(db_name)==0: db_name=network.split("-")[2]

    _dao=DAO(db_loc,db_name)
    if _dao.isConnected():
      rc=_dao.lazy_mint(nft,"",application_root)
    else:
      log("Impossible de se connecter à "+db_loc+"/"+db_name)


  if "file" in network.lower():
    if not storagefile.startswith(TEMP_DIR): storagefile=TEMP_DIR+storagefile
    storefile=StoreFile(storagefile)
    rc=storefile.lazymint(nft)
    storefile.export_to_yaml()

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

  if ("result" in rc) and ("transaction" in rc["result"]) and (network!="file"):
    dao.add_histo(request.args.get("ope",""),"mint",miner,collection_id,rc["result"]["transaction"],network,"Minage")

  return rc




def activity_report_sender(app,dest:str,event:str="CR d'activité"):
  """
  Envoi un mail sur l'activité du serveur
  :param activity_report_dest:
  :param domain_server:
  :param domain_appli:
  :param event:
  :return:
  """
  domain_server=app.config["DOMAIN_SERVER"]
  domain_appli=app.config["DOMAIN_APPLI"]
  log(event)
  mail=open_html_file("mail_activity_report",{
    "DOMAIN_SERVER":domain_server,
    "DOMAIN_APPLI":domain_appli,
    "event":event
  })

  if not "localhost" in domain_server and not "127.0.0.1" in domain_server:
    send_mail(mail,_to=dest,subject="ACTIVITY REPORT de "+domain_server+" - "+event[:60])
  else:
    log(mail)



