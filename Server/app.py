import atexit
import pickle
import urllib.parse
import base64
import csv
import datetime
import json
import os
import ssl
import sys
import urllib
from asyncio import sleep
from copy import copy
from io import BytesIO, StringIO
from os import listdir
from os.path import exists
from random import random
from xml.dom import minidom
from xml.dom.minidom import Element
from zipfile import ZipFile

from flask_socketio import SocketIO

from Polygon.Polygon import Polygon, POLYGON_KEY_DIR
from StoreFile import StoreFile
from TokenForge import upload_on_platform
from Tools import get_operation, decrypt, get_access_code_from_email, send, convert_to

import py7zr
import pyqrcode
import requests
import yaml
from PIL.Image import Image
from apscheduler.schedulers.background import BackgroundScheduler
from bson import ObjectId
from flask import request, jsonify, send_file, Flask, make_response
from flask_cors import CORS
from werkzeug.datastructures import FileStorage
from yaml import dump

import GitHubStorage
from ArtEngine import ArtEngine, Layer, Sticker
from Elrond.Elrond import Elrond, ELROND_KEY_DIR
from NFT import NFT
from PrestaTools import PrestaTools
from Solana.Solana import SOLANA_KEY_DIR, Solana
from Tools import setParams, get_access_code, check_access_code, get_fonts
from Tools import log, now, is_email, send_mail, open_html_file, encrypt
from TransactionsGraph import TransactionsGraph
from dao import DAO
from ipfs import IPFS
from secret import GITHUB_TOKEN, GITHUB_ACCOUNT, PERMS, SECRET_JWT_KEY, SECRETS_FILE, SECRET_ACCESS_CODE
from flask_jwt_extended import create_access_token, JWTManager

from settings import DBSERVER_SYSTEM, DBNAME_SYSTEM, IPFS_SERVER

scheduler = BackgroundScheduler()
log("Initialisation du scheduler ok")

app = Flask(__name__)
log("Initialisation de l'app ok")

socketio = SocketIO(app,cors_allowed_origins="*")
log("Initialisation de la websocket")

nft=ArtEngine()
log("Initialisation de l'ArtEngine ok")

dao=DAO(DBSERVER_SYSTEM,DBNAME_SYSTEM+"_debug" if "debug" in sys.argv else "")
log("Initialisation de la base de donnée OK")

#voir la documentation de metaboss:



def returnError(msg:str="",_d=dict(),status=500):
  log("Error "+msg)
  return "Ooops ! Petit problème technique. "+msg,status



#http://127.0.0.1:9999/api/update/?account=GwCtQjSZj3CSNRbHVVJ7MqJHcMBGJJ9eHSyxL9X1yAXy&url=
#TODO: ajouter les restrictions d'appel
@app.route('/api/update/')
#https://metaboss.rs/set.html
def update():
  url=request.args.get("url")
  account=request.args.get("account")
  return exec("update","uri --new-uri "+url,account=account)


@app.route('/api/palettes/',methods=["GET"])
def get_palettes():
  palette=json.load(open("./palettes.json","r"))
  return jsonify(palette)



@app.route('/api/getyaml/<name>/')
@app.route('/api/getyaml/<name>/<format>/')
#http://127.0.0.1:4242/api/getyaml/calvi22/txt/?dir=Operations
def getyaml(name:str):
  dir=request.args.get("dir",".")
  format=request.args.get("format","json")

  if name.startswith("b64:"):name=str(base64.b64decode(name[4:]),"utf8")
  if name.startswith("http"):
    return jsonify(yaml.load(name,Loader=yaml.FullLoader))

  filename=dir+"/"+name+(".yaml" if not name.endswith(".yaml") else "")
  f=open(filename,"r",encoding="utf-8")

  try:
    rc=yaml.safe_load(f.read())
  except Exception as inst:
    return returnError("Probleme de format du fichier "+name+" "+str(inst.args))

  if format=="json":
    return jsonify(rc),200

  #retourne au format txt
  s=yaml.dump(rc,default_flow_style=False,indent=4,encoding="utf8")
  f.close()
  return s



@app.route('/api/perms/<addr>/',methods=["GET"])
def get_perms(addr:str):
  if not addr in PERMS: addr="anonymous"
  d=copy(PERMS[addr])
  if "copy_from" in d: d=PERMS[d["copy_from"]]

  perm=request.args.get("perm","")
  if len(perm)==0:
    d["perms"]=d["perms"]+PERMS["anonymous"]["perms"]
    return jsonify(d)
  else:
    if perm in d["perms"]:
      return jsonify({"access":True})
    else:
      return jsonify({"access":False})








@app.route('/api/clone_with_color/',methods=["POST"])
def clone_with_color():
  body=request.json
  l=nft.get_layer(body["layer"]["name"])
  format=request.args.get("format","webp")

  rc=[]
  for elt in l.elements:
    if type(elt)==Sticker:
      for color in list(body["palette"].values()):
        log("Clone pour la couleur "+color)
        img:Image=elt.replace_color(body["color"],color)

        buffered = BytesIO()
        img.save(buffered, format=format)
        rc.append("data:image/"+format.lower()+";base64,"+str(base64.b64encode(buffered.getvalue()),"utf8"))

  return jsonify(rc)







@app.route('/api/reset_collection/',methods=["GET"])
#test http://127.0.0.1:4242/api/test/
def reset_collection():
  nft.reset()
  return jsonify({"status":200})


@app.route('/api/fonts/',methods=["GET"])
#test http://127.0.0.1:4242/api/fonts/
def api_get_fonts():
  return jsonify({"fonts":get_fonts()})



@app.route('/api/layers/',methods=["POST"])
def layers(body=None):
  """
  charge les couches dans l'instance partagé nft
  :tags: add_layer
  :param body:
  :return:
  """
  if body is None: body=request.json
  if not "name" in body:
    return "Syntaxe error for this layer",500
  name=body["name"]
  limit=int(request.args.get("limit","0"))
  log("Generation de la couche "+name)
  nft.delete(name) # <-- TODO: cette instance ne devrait plus être partagés dans une optique multi-usage
  position=body["position"] if "position" in body else 0
  layer=Layer(name,
              position=position,
              unique=(body["unique"] if "unique" in body else False),
              indexed=(body["indexed"] if "indexed" in body else True)
              )

  elts=body["elements"]
  if limit>0: elts=elts[0:limit]
  s=None
  for elt in elts:
    s=None
    log("Traitement de "+str(elt))
    if elt:
      if "text" in elt and elt["text"]:
        s=Sticker(text=elt["text"]["text"],x=elt["text"]["x"],y=elt["text"]["y"],
                  dimension=(elt["text"]["dimension"][0],elt["text"]["dimension"][1]),
                  fontstyle=elt["text"]["fontstyle"])
      else:
        if elt["image"] and len(elt["image"])>0:
          ext=elt["image"].split("?")[1] if "?" in elt["image"] else elt["image"][elt["image"].rindex(".")+1:]
          name=elt["image"].split("images/")[1].split("_0x")[0]
          s=Sticker(name=name,image=elt["image"],ext=ext,dimension=(body["width"],body["height"]))

      if s:
        layer.add(s)

  log("Fin de generation de "+layer.name)
  nft.add(layer)

  to_show=int(request.args.get("preview","0"))
  if s:
    rc=[]
    for s in layer.elements:

      if len(rc) % 10==0:log(str(len(rc))+" élements assemblés")
      #factor=1 if s.text is None else 200/body["width"]
      rc.append({
        "text":s.text,
        "image":s.toBase64("webp",1) if to_show>0 else ""
      })

      if s.text is not None:s.clear()
      to_show=to_show-1

    log("Fin de traitement des images")
    return jsonify({"status":200,"elements":rc})
  else:
    return jsonify({"status":200})




@app.route('/api/generate_svg/',methods=["POST"])
def generate_svg():
  rc=list()
  _data=request.json
  master=Sticker(image=_data["file"],ext="svg")

  #voir https://docs.python.org/fr/3/library/xml.dom.html#dom-element-objects
  doc=minidom.parseString(master.text["text"])
  bCreateFromMaster=False
  for elt in doc.getElementsByTagName("desc"):
    for node in elt.childNodes:
      if len(node.data.split("|"))>1:
        bCreateFromMaster=True
        for text in node.data.split("|"):
          s=master.clone()
          pere:Element=node.parentNode.parentNode
          pere.getElementsByTagName("tspan")[0].childNodes[0].data=text
          s.text["text"]=doc.toxml()
          file=s.render_svg(with_picture=False,prefix_name="svg")
          rc.append(app.config["DOMAIN_SERVER"]+"/api/images/"+file)

  if not bCreateFromMaster:
    rc.append(app.config["DOMAIN_SERVER"]+"/api/images/"+master.image)

  # if "_idx_" in master.text["text"] or "_text_" in master.text["text"]:
  #   limit=len(_data["sequence"])
  #   for index in range(limit):
  #     replacements={
  #       "idx":index+1,
  #       "text": _data["sequence"][index]
  #     }
  #     s=master.clone()
  #     file=s.render_svg(dictionnary=replacements,
  #                       with_picture=False,
  #                       prefix_name="svg")
  #     rc.append(app.config["DOMAIN_SERVER"]+"/api/images/"+file)
  # else:
  #   rc.append(app.config["DOMAIN_SERVER"]+"/api/images/"+master.image)

  return jsonify(rc)


@app.route('/api/collections/<addresses>/')
#test http://127.0.0.1:4242/api/collection/herve
def get_collections(addresses:str):
  """
  retourne l'ensemble des collections appartenant à un utilisateur
  :param owner:
  :return:
  """
  network=request.args.get("network","elrond-devnet")
  with_detail=(request.args.get("detail","true")=="true")
  cols=[]
  for addr in addresses.split(","):
    if "elrond" in network: cols=cols+Elrond(network).get_collections(addr,with_detail)
    if "polygon" in network: cols=cols+Polygon(network).get_collections(addr)

  return jsonify(cols)




@app.route('/api/collection/')
def get_collection(limit=100,format=None,seed=0,size=(500,500),quality=100,data={},ext="webp"):
  """
  Generation de la collection des NFTs
  :param limit:
  :param format:
  :param seed:
  :param ext:
  :param size:
  :return:
  """
  rc=[]
  if format!="list": #Dans le cas de format = list cette fonction est appelé depuis le serveur (pas depuis une api)
    limit=int(request.args.get("limit",10))
    size=request.args.get("size","500,500").split(",")
    format=request.args.get("format","zip")
    quality=request.args.get("quality",98)
    seed=int(request.args.get("seed","0"))
    ext=request.args.get("image","webp")
    data=request.args.get("data","")
    attributes=request.args.get("attributes","")
    nft.name=request.args.get("name","mycollection").replace(".png","")
    target_platform=request.args.get("platform","")

  log("On détermine le nombre d'image maximum générable")
  max_item=1
  must_register_font=False
  for layer in nft.layers:
    if layer.indexed:
      max_item=max_item*len(layer.elements)
    for elt in layer.elements:
      if elt.ext=="SVG":
        must_register_font=True


  if type(data)!=dict:
    s_data= urllib.parse.unquote(str(base64.b64decode(data), "utf8"))
    _d=json.loads(s_data)
  else:
    _d=data
    s_data=""

  if must_register_font: nft.register_fonts()

  prefix="gen_"+now("random").replace("0x","")
  files=nft.generate(
    dir="./temp/",
    limit=min(limit,max_item),
    seed_generator=seed,
    width=int(size[0]),
    height=int(size[1]),
    quality=quality,
    data=s_data,
    ext=ext,
    attributes= json.loads(urllib.parse.unquote(str(base64.b64decode(attributes), "utf8"))) if len(attributes)>0 else [],
    prefix=prefix,
    target_platform=target_platform if format=="upload" else ""
  )

  for f in os.listdir("./temp"):
    try:
      if f.startswith(prefix):os.remove("./temp/"+f)
    except:
      log("Impossible de supprimer "+f)



  archive_file="Collection_"+now("hex")+".7z"
  with py7zr.SevenZipFile("./temp/"+archive_file, 'w') as archive:
    for f in files:
      archive.write(f)

  if format=="list":
    return files

  # if format=="upload":
  #   platform=request.args.get("platform","nftstorage")
  #   for filename in files:
  #     _f=open(filename,"rb")
  #     only_filename=filename[filename.rindex("/")+1:]
  #     obj={
  #       "content":"data:image/jpeg;base64,"+str(base64.b64encode(_f.read()),"utf8"),
  #       "type":"image/"+ext,
  #       "filename":only_filename
  #     }
  #     rc.append(upload_on_platform(obj,platform))
  #     _f.close()


  for filename in files:
    f=open(filename,"rb")
    only_filename=filename[filename.rindex("/")+1:]
    rc.append({"src":"data:image/jpeg;base64,"+str(base64.b64encode(f.read()),"utf8"),"filename":only_filename})
    f.close()
    os.remove(filename)


  return jsonify({"preview":rc,"archive":archive_file})



@app.route('/api/send_photo_for_nftlive/<conf_id>/',methods=['POST'])
def send_photo_for_nftlive(conf_id:str):

  config=configs(conf_id,format="dict")
  if len(config)==0:
    return returnError("Configuration "+conf_id+" introuvable")
  else:
    config=config[0]

  image=request.json["photo"]
  dim=request.json["dimensions"] if "dimensions" in request.json else str(config["width"])+"x"+str(config["height"])
  limit=request.json["limit"] if "limit" in request.json else config["limit"]
  quality=request.json["quality"] if "quality" in request.json else 90
  note=request.json["note"] if "note" in request.json else ""
  seq=request.json["sequence"] if "sequence" in request.json else []

  dyna_fields=dict()
  for field in request.json["dynamic_fields"] if "dynamic_fields" in request.json else []:
    dyna_fields[field["name"]]=field["value"]

  nft.reset()
  nft.add(Layer("maphoto",position=0))
  nft.add_image_to_layer("maphoto",image)
  for layer in config["layers"]: layers(layer)

  dir="./temp/"
  files=nft.generate(
    dir=dir,
    limit=int(limit),
    seed_generator=0,
    width=int(dim.split("x")[0]),
    height=int(dim.split("x")[1]),
    quality=quality,
    data=note,
    ext="webp",
    replacements=dyna_fields
  )
  files=[x.replace(dir,"") for x in files]

  return jsonify({"images":files})







@app.route('/api/nftlive_access/<addr>/')
def nftlive_access(addr:str):
  """
  Consiste à vérifier l'accès à NFT live
  :param addr: addr du demandeur
  :return: l'ensemble des opérations auquel il peut prétendre
  """

  network=request.args.get("network","elrond-devnet")
  nfts=[]
  if(addr.startswith("erd")):
    elrond:Elrond=Elrond(network)
    nfts=elrond.get_nfts(elrond.toAccount(addr),with_attr=False)
    nfts=elrond.complete_collection(nfts)

  rc=[]
  for ope in get_operations():
    if "nftlive" in ope:
      for nft in nfts:
        if nft.collection["id"] in ope["nftlive"]["collections"]:
          if not ope in rc:rc.append(ope)

  return jsonify(rc)






@app.route('/api/infos/')
#test http://127.0.0.1:4242/api/infos/
#test http://75.119.159.46:4242/api/infos/
#test https://server.f80lab.com:4242/api/infos/
def infos():
  rc={"Solana":{"keys":len(Solana("devnet").get_keys())},
      "Elrond":{"keys":len(Elrond("devnet").get_keys())},
      "Secret":{},
      "Database":{
        "tokens":dao.db["nfts"].count_documents(filter={}),
        "validators":dao.db["validators"].count_documents(filter={}),
        "mintpool":dao.db["mintpool"].count_documents(filter={})
      }
      }
  return jsonify(rc)





@app.route('/api/get_nft_from_db/',methods=["GET"])
def get_nft_from_db():
  id=request.args.get("id")
  return jsonify(dao.get(id))



@app.route('/api/test/',methods=["GET"])
#http://127.0.0.1:4242/api/test
def test():
  pass



@app.route('/api/analyse_transaction/<address>/',methods=["GET"])
#test http://127.0.0.1:4242/api/analyse_transaction/erd16ck62egnvmushkfkut3yltux30cvp5aluy69u8p5hezkx89a2enqf8plt8/?limit=200&profondeur_max=5&network=elrond-devnet&size=50
def analyse_transaction(address:str):
  elrond=Elrond(request.args.get("ope","elrond-devnet"))
  if not address: return returnError("Pas d'adresse de départ")

  limit=int(request.args.get("limit","100"))
  profondeur_max=int(request.args.get("profondeur_max","10"))
  format=request.args.get("format","graph")
  methods=request.args.get("methods","ESDTNFTCreate,MultiESDTNFTTransfer,ESDTTransfer,issueNonFungible,ESDTNFTTransfer").split(",")
  exclude_addresses=request.args.get("exclude","erd1qqqqqqqqqqqqqqqpqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqzllls8a5w6u").split(",")

  elrond.transactions.clear()
  if address.startswith("erd"):
    elrond.get_transactions(address,
                            limit=limit,
                            size=int(request.args.get("size","50")),
                            profondeur=0,
                            profondeur_max=profondeur_max,methods=methods,
                            exclude_addresses=exclude_addresses)
  else:
    elrond.get_transactions_from_collection(address,int(request.args.get("size","500")))

  if format.startswith("transaction"):
    return jsonify({"transactions":elrond.transactions})

  if format=="graph":
    G=TransactionsGraph()
    keys=elrond.get_keys()
    for t in elrond.transactions:
      t["to"]=elrond.find_alias(t["to"],keys)
      t["from"]=elrond.find_alias(t["from"],keys)

    G.load(elrond.transactions)

  return jsonify({"graph":G.export()})





@app.route('/api/analyse_prestashop_orders/',methods=["GET"])
#test http://127.0.0.1:4242/api/analyse_prestashop_orders/?ope=main_devnet
def analyse_prestashop_orders():
  _operation=get_operation(request.args.get("ope"))
  _store_section=_operation["store"]
  prestashop=PrestaTools(_store_section["prestashop"]["api_key"],_store_section["prestashop"]["server"],_store_section["prestashop"]["language"])
  nfts=prestashop.analyse_order()
  for nft in nfts:
    new_owner=nft.other["owner"]
    mint(nft,nft.other["miner"] if "miner" in nft.other else "",new_owner,nft.network)
    prestashop.update_order_status(nft.other["order_id"],4) #Passage de la commande au statut expédié

  return jsonify({"message":"traitement terminé"})


@app.route('/api/export_to_prestashop/',methods=["GET",'POST'])
#test http://127.0.0.1:4242/api/export_to_prestashop/?root_category=1&ope=main_devnet&api
def export_to_prestashop():
  """
  htag: transfer_to_prestashop
  :return:
  """
  _operation=get_operation(request.args.get("ope"))
  _store_section=_operation["store"]
  collection_filter:bool=(request.args.get("collection_filter","true")=="true") #Permet d'exlure le filtre du fichier d'opération

  prestashop=PrestaTools(_store_section["prestashop"]["api_key"],_store_section["prestashop"]["server"],_store_section["prestashop"]["language"])
  root_category=prestashop.find_category(_store_section["prestashop"]["root_category"]["name"] or "NFTs")
  if root_category is None:
    log("La catégorie root pour les NFT n'existe pas encore dans prestashop")
    root_from_operation=_store_section["prestashop"]["root_category"]
    root_category=prestashop.add_category(
      root_from_operation["name"],
      2,
      root_from_operation["description"])

  categories=dict()
  log("Création des collections sous forme de categorie dans Prestashoo")

  if request.method=="GET":
    nfts=get_nfts_from_src(_operation["data"]["sources"],with_attributes=True)
  else:
    nfts=[NFT(object=request.json)]

  if "filter" in _store_section:
    if "from" in _store_section["filter"]:
      nfts=nfts[_store_section["filter"]["from"]:_store_section["filter"]["to"]]

  for nft in nfts:
    if nft.collection not in categories.keys():
      log("Traitement de la collection "+nft.collection)
      ref_col=prestashop.find_category_in_collections(nft.collection,_operation["collections"])
      if ref_col is None:
        log(nft.collection+" n'existe pas dans prestashop")
        ref_col={"name":nft.collection,"description":"","price":0}

    store_col=prestashop.find_category_in_collections(nft.collection,_operation["store"]["collections"])
    if not collection_filter or not store_col is None: #cette collection n'est pas dans les collections à inclure dans la boutique
      c=prestashop.find_category(nft.collection)
      if c is None:
        log("La catégorie "+nft.collection+" n'existe pas dans prestashop. On la créé")
        c=prestashop.add_category(
          ref_col["name"],
          root_category["id"],
          ref_col["description"]
        )
      else:
        log("La catégorie "+nft.collection+" est bien présente dans prestashop")

      categories[c["name"]]={
        "price":store_col["price"] if store_col and "price" in store_col else ref_col["price"],
        "name":ref_col["name"],
        "id":c["id"]
      }

    else:
      log("Le NFT "+nft.name+" de la collection "+nft.collection+" n'est pas dans les collections à exporter du fichier d'opération")


  for nft in nfts:
    if nft.collection in categories.keys():

      features={
        "address":nft.address,
        "network":nft.network,
        "operation":_operation["id"],
        "royalties":str(nft.royalties),
        "visual":nft.visual,
        "creators":" ".join([_c["address"]+"_"+str(_c["share"]) for _c in nft.creators])
      }

      if not nft.is_minted():
        features["miner"]=_operation["lazy_mining"]["miner"]
      else:
        features["owner"]=nft.owner

      product=prestashop.add_product(nft=nft,on_sale=True,
                                     operation_id=_operation["id"],
                                     features=features,
                                     tags=["NFT"]
                                     )
      if product is None:
        return returnError("Impossible de créer "+nft.toString())
      else:
        prestashop.set_product_quantity(product,nft.get_quantity())
        filename="./temp/image"+now("hex")+".gif"
        try:
          #buf_image=convert_to_gif(nft.visual,filename=filename)
          sleep(3)
        except:
          log("Impossible de convertire l'image")

        prestashop.add_image(product["id"],filename)
        os.remove(filename)

  return jsonify({"message":"ok"})





@app.route('/api/send_conf/',methods=["POST"])
#test http://127.0.0.1:4242/api/send_conf/
def send_conf():
  data=request.json
  #TODO: envoie de l'email de confirmation à coder
  return jsonify({"error":""})


@app.route('/api/tables/<table>',methods=["GET","DELETE"])
#test http://127.0.0.1:4242/api/tables/nfts
def tables(table:str):
  if request.method=="GET":
    try:
      rows=dao.db[table].find()
    except:
      return jsonify([])

    rc=[]
    for row in rows:
      del row["_id"]
      for exclude in request.args.get("excludes","").split(","):
        if len(exclude)>0 and exclude in row: del row[exclude]
      for k in row.keys():
        if type(row[k])==dict or type(row[k])==bytes:
          row[k]=str(row[k])

      rc.append(row)

  if request.method=="DELETE":
    dao.db[table].drop()
    rc={"error":""}

  return jsonify(rc)



def get_operations() -> [dict]:
  """
  retourne l'ensemble des opérations disponibles sur le serveur
  :return:
  """
  rc=[]
  for name in listdir("./Operations"):
    if name.endswith(".yaml"):
      rc.append(get_operation(name))
  return rc



@app.route('/api/transfer_to/<nft_addr>/<to>/<owner>/',methods=["POST"])
def transfer_to(nft_addr:str,to:str,owner:str):
  network=request.args.get("network","elrond-devnet")
  mail_content=request.json["mail_content"] or "mail_new_account"

  if "solana" in network:
    solana=Solana(network)
    if "@" in to:
      words,to,secret_key,secret_key_ints=solana.create_account(to,domain_appli=app.config["DOMAIN_APPLI"],network=network)
    rc=solana.transfer(nft_addr,to,owner)

  if "elrond" in network:
    elrond=Elrond(network)
    if not elrond.find_key(owner):
      return returnError("Impossible de transférer sans la clé secret du propriétaire "+owner)

    collection_id,nonce=elrond.extract_from_tokenid(nft_addr)
    if "@" in to:
      to,pem,words,qrcode=elrond.create_account(to,
                                                domain_appli=app.config["DOMAIN_APPLI"],
                                                network=network,
                                                mail_content=mail_content)

    t=elrond.transfer(collection_id,nonce,elrond.toAccount(owner),to)
    nfluent_wallet=elrond.nfluent_wallet_url(to,network)
    rc=(not t is None)

  if rc:
    return jsonify({"error":"","message":"NFT transféré","nfluent_wallet":nfluent_wallet})
  else:
    return returnError("Probleme de transfert")




@app.route('/api/action_calvi/',methods=["POST"])
def action():
  """
  validation des NFT pour l'opération calvi
  :return:
  """
  body=request.json
  operation=get_operation(body["operation"])

  # if body["operateur"]!="4271" and not body["operateur"] in operation["validate"]["access_codes"]:
  #   log("Opérateur non autorisé")
  #   return jsonify({"error":"1"})

  attrs=body["offchain"]["attributes"]
  nbPass=int(request.args.get("nb_pass","2"))
  idx_date=-1
  for idx_date in range(len(attrs)):
    if attrs[idx_date]["trait_type"]=="Last use":
      if "value" in attrs[idx_date]:
        year=attrs[idx_date]["value"][attrs[idx_date]["value"].rindex("/")+1:]
        if datetime.datetime.now().year>=int(year):
          return jsonify({"error":"","status":"ko","message":"Ce NFT a déjà été utilisé cette année pour retirer les passes"})
      break

  if idx_date==-1:
    attrs.append({"trait_type":"Dernière modification"})
    idx_date=len(attrs)-1

  for key in ["Edition"+str(i) for i in range(1,5)]:
    for a in attrs:
      if a["trait_type"]==key and int(a["value"])>=nbPass:
        a["value"]=int(a["value"])-nbPass
        attrs[idx_date]["value"]=datetime.datetime.now().strftime("%d/%m/%Y")

        section_method=operation["validate"]["method"]
        if section_method["update_token"]:
          if "solana" in body["network"]:
            id=body["uri"][body["uri"].rindex("/")+1:]+"_"+str(now())
            rc=upload_on_platform(body["offchain"],section_method["storage"],id,{"repository":section_method["repository"]})
            #TODO: Ajouter la destruction de l'ancien fichier
            #private_key=decrypt(operation["accounts"][operation["network"].split("-")[0]][section_method["update_authority"]])
            keyfile=section_method["update_authority"]
            tx=Solana(operation["network"]).exec("update","uri --new-uri "+rc["url"],account=body["token"],keyfile=keyfile)
          else:
            keyfile=section_method["update_authority"]
            body["offchain"]["attributes"]=attrs
            tx=Elrond(body["network"]).update(keyfile,body["token"],body["offchain"],IPFS(IPFS_SERVER))

          tx_log=tx["error"] if len(tx["error"])>0 else tx["result"]["transaction"]

          dao.add_histo(
            operation["id"],
            "update_nft",
            keyfile,
            "",
            tx_log,
            body["network"],
            "MAJ du lien data offchain par "+body["operateur"],
            [body["token"],body["operateur"]]
          )

          if len(tx["error"])>0: return jsonify({"error":"2","message":tx["error"]})
        else:
          log("Modification direct du fichier")
          if section_method["storage"]=="github":
            rc=GitHubStorage.GithubStorage(section_method["repository"],"main",GITHUB_ACCOUNT,GITHUB_TOKEN).add(body["offchain"],body["uri"],True)
            dao.add_histo(operation["id"],
                          "update_metadata_file",
                          GITHUB_ACCOUNT,"",
                          rc,
                          operation["network"],
                          "MAJ direct du data offchain",
                          [body["token"]]
                          )


        return jsonify({
          "error":"0",
          "cid":rc["cid"],
          "url":rc["url"],
          "status":"ok",
          "message":"Le NFT est à jour. Vous pouvez distribuer "+str(nbPass)+" passe(s)"
        })

  return jsonify({"error":"","status":"ko","message":"Aucun passe disponible pour ce nft"})




@app.route('/api/operations/',methods=["GET","POST"])
@app.route('/api/operations/<ope>/',methods=["DELETE","GET"])
#test http://127.0.0.1:4242/api/operations/
#test http://127.0.0.1:4242/api/operations/calvi22
def manage_operations(ope=""):
  format=request.args.get("format","json")
  if request.method=="GET":
    if len(ope)>0:
      rc=get_operation(ope.strip())
    else:
      rc=[]
      for o in os.listdir("./Operations"):
        if o.endswith("yaml"):
          with open("./Operations/"+o,"rb") as file:
            _opes= yaml.load(file, Loader=yaml.FullLoader)
            _opes["filename"]=o
            rc.append(_opes)

          if ope.lower()==_opes["id"].lower():
            rc=_opes
            break

    if rc and type(rc)==dict and "validate" in rc and "users" in rc["validate"]:
      rc["validate"]["access_codes"]=[]
      if rc["validate"]["users"]:
        for user in rc["validate"]["users"]:
          rc["validate"]["access_codes"].append(get_access_code_from_email(user))


  if request.method=="POST":
    with open("./Operations/"+request.json["filename"],"w",encoding="utf8") as file:
      body=str(base64.b64decode(request.json["file"].split("base64,")[1]),"utf8") if request.json["file"].startswith("data:") else request.json["file"]
      file.write(body)
    rc={"error":""}

  if request.method=="DELETE":
    os.remove("./Operations/"+ope)
    rc={"error":""}

  if format=="json":
    return jsonify(rc)
  else:
    filename=rc["id"]+".yaml"
    del rc["access_codes"]
    s=bytes(dump(rc),"utf8")
    return send_file(BytesIO(s),as_attachment=True,attachment_filename=filename)



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
      with open("./Operations/"+ope+(".yaml" if not ope.endswith(".yaml") else ""),"r") as file:
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
  nfts=[]
  for src in srcs:
    if src["active"]:
      log("Récupération des nfts depuis "+str(src))

      if not "filter" in src:src["filter"]={}
      if not "limit" in src["filter"]: src["filter"]["limit"]=10000

      if src["type"] in ["database","db"]:
        try:
          if collections and len(collections)>0:
            for collection in collections:
              if dao.connect(src["connexion"],src["dbname"]):
                l_nfts=list(dao.nfts_from_collection(collection))
                nfts=nfts+l_nfts[:src["filter"]["limit"]]
                src["ntokens"]=len(l_nfts)
          else:
            #Si le filtre sur les collections n'a pas été précisé ou si vide, on prend tous les NFTs des sources
            if dao.connect(domain=src["connexion"],name=src["dbname"]):
              l_nfts=list(dao.nfts_from_collection(None))
              nfts=nfts+l_nfts[:src["filter"]["limit"]]

          src["ntokens"]=len(l_nfts)
        except:
          log("Probleme de lecture de "+src["connexion"])


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



      if src["type"]=="config":
        config=configs(src["connexion"],format="dict")
        for layer in config["layers"]: layers(layer)

        files=get_collection(
          size=(config["width"],config["height"]),
          format="list",
          seed=src["seed"] if "seed" in src else 1,
          limit=src["limit"] if "limit" in src else 10,
          data={
            "title":"MonTitre",
            "symbol":"token__idx__",
            "description":"madescription",
            "collection":"macollection",
            "properties":"propriete=valeur",
            files:"http://monfichier"
          }
        )
        for file in files:
          id=file[file.rindex("/")+1:]
          nfts.append({
            "uri":file,
            "image":app.config["DOMAIN_SERVER"]+"/api/images/"+id,
            "id":id,
            "creators":[{"address":x} for x in src["creators"]]
          })

  return nfts






@app.route('/api/save_privacy/',methods=["POST"])
#test http://127.0.0.1:4242/api/get_tokens_for_dispenser/calvi22_devnet?limit=10
def save_privacy():
  data:dict=request.json

  secrets=dict()
  if exists(SECRETS_FILE):
    with open(SECRETS_FILE,"rb") as file:
      secrets = pickle.load(file)

  secrets[data["addr"]]=data["secret"]
  with open(SECRETS_FILE,"wb") as file2:
    pickle.dump(secrets,file2)

  return jsonify({"message":"ok"})



@app.route('/api/get_tokens_to_send/<ope>/',methods=["GET"])
#test http://127.0.0.1:4242/api/get_tokens_for_dispenser/calvi22_devnet?limit=10
def get_tokens_to_send(ope:str):
  section=request.args.get("section","dispenser")
  _opes=open_operation(ope)
  if _opes is None:return jsonify({"error":"operation unknown"})

  limit=int(request.args.get("limit","100000"))
  nfts=get_nfts_from_src(_opes["data"]["sources"],_opes[section]["collections"])
  nfts=nfts[:limit]

  return jsonify([nft.__dict__ for nft in nfts])




@app.route('/api/key/<code>',methods=["GET"])
@app.route('/api/qrcode/',methods=["GET"])
@app.route('/api/qrcode/<code>',methods=["GET"])
def get_key(code=""):
  format=request.args.get("format","qrcode")
  scale=request.args.get("scale",9)

  if len(code)==0: code=request.args.get("code","")

  buffer=BytesIO()
  pyqrcode.create(code).png(buffer,scale=scale)

  if format=="json":
    return jsonify({"qrcode":"data:image/png;base64,"+str(base64.b64encode(buffer.getvalue()),"utf8")})

  if format=="qrcode" or format=="image":
    response = make_response(buffer.getvalue())
    response.headers.set('Content-Type', 'image/png')
    return response



@app.route('/api/check_access_code/<code>',methods=["GET"])
def api_check_access_code(code:str):
  """
  Vérifie l'access code des validateurs
  :param code:
  :return:
  """
  addr=check_access_code(code)
  if addr is None:
    return returnError("Code incorrect")
  else:
    return jsonify({"address":addr})


@app.route('/api/mintpool/',methods=["GET"])
@app.route('/api/minerpool/',methods=["GET"])
@app.route('/api/minerpool/<id>/',methods=["DELETE","POST"])
# http://127.0.0.1:4242/api/minerpool/
def get_minerpool(id=""):
  """
  retourne le contenu de la pool de minage pour les NFTs obtenus via la dealermachine
  :param id:
  :return:
  """
  asks=dao.db["mintpool"].find()
  rc=[]
  if request.method=="POST":
    rc={"updated":dao.edit_pool(ObjectId(id),None,"")}

  if request.method=="GET":
    for ask in list(asks):
      ask["id"]=str(ask["_id"])
      del ask["_id"]
      rc.append(ask)

  if request.method=="DELETE":
      tx=dao.db["mintpool"].delete_one({"_id":ObjectId(id)})
      rc={"deleted":tx.deleted_count}

  return jsonify(rc)


def async_mint(nbr_items=3,filter=""):
  if not dao.isConnected():
    log("Impossible de se connecter à la base")
  else:
    for ask in dao.get_nfts_to_mint(int(nbr_items),filter):
      log("Traitement de la demande "+str(ask["_id"]))
      dao.edit_pool(ask["_id"],now(),"traitement en cours")
      nfts=get_nfts_from_src(ask["sources"],ask["filter"],False)

      nft_to_mint=None
      elrond=Elrond(ask["network"])
      _miner=elrond.toAccount(ask["miner"])

      if len(nfts)>0:
        log("Tirage au sort d'un NFT parmis la liste de "+str(len(nfts)))
        for i in range(200):
          nft_to_mint=nfts[int(random()*len(nfts))]

          if nft_to_mint.owner=="":
            if elrond.canMint(nft_to_mint): break
          else:
            if not _miner is None and nft_to_mint.owner==_miner.address.bech32(): break
      else:
        log("Aucun NFT à miner")

      if not nft_to_mint is None:
        log("Minage de "+nft_to_mint.name+" en cours")
        if _miner is None:
          log("Le miner est fixé sur le propriétaire de la collection "+nft_to_mint.collection["id"])
          _miner=elrond.toAccount(nft_to_mint.collection["owner"])

        log("Ajout de l'attribut lazymint pour ne pas risquer de re-minté")
        nft_to_mint.attributes.append({"trait_type":"lazymint","value":nft_to_mint.address})
        rc=mint(nft_to_mint,_miner.address.bech32(),ask["dest"],ask["network"],wallet_appli=ask["wallet"])
        if not rc or rc["error"]!="":
          log("Problème de minage voir "+rc["hash"])
          message="Error"+rc["error"]+" voir "+rc["hash"]
        else:
          message="Ok: "+rc["hash"]

        log("Mise a jour des données de la pool de minage")
        dao.edit_pool(ask["_id"],now(),message)

      else:
        log("Aucun NFT disponible pour le minage")
        dao.edit_pool(ask["_id"],now(),"Error: Aucun NFT disponible pour le minage")


# http://127.0.0.1:4242/api/async_mint/3/
@app.route('/api/async_mint/<nbr_items>/',methods=["GET"])
def api_async_mint(nbr_items:str="3"):
  async_mint(nbr_items=int(nbr_items),filter=request.args.get("filter",""))
  return jsonify({"message":"ok"})






@app.route('/api/add_user_for_nft/',methods=["POST"])
def add_user_for_nft():
  """
  Insere une demande de minage ou transfert d'un NFT d'une collection
  :return:
  """
  id=dao.add_nft_to_mint(
                      miner=request.json["miner"],
                      sources=request.json["operation"]["data"]["sources"],
                      network=request.json["network"],
                      collections=request.json["collections"],
                      destinataires=request.json["owner"],
                      wallet=request.json["wallet"])

  return jsonify({"message":"ok","ask_id":id})



@app.route('/api/access_code/<addr>',methods=["GET"])
def api_access_code(addr=""):
  """
  fournir le code d'accès pour l'usage de nfluent_wallet_connect
  :param addr:
  :return:
  """
  format=request.args.get("format","base64")
  scale=request.args.get("scale",9)

  if len(addr)>0:

    buffer=BytesIO()
    access_code=get_access_code(addr)
    pyqrcode.create(access_code).png(buffer,scale=scale)

    if format=="qrcode":
      response = make_response(buffer.getvalue())
      response.headers.set('Content-Type', 'image/png')
      return response

    if format=="base64":
      return jsonify({
        "image":"data:image/png;base64,"+str(base64.b64encode(buffer.getvalue()),"utf8"),
        "access_code":str(access_code,'utf-8')
      })







#test http://127.0.0.1:4242/api/get_new_code/demo?format=qrcode
#http://127.0.0.1:4242/api/get_new_code/demo/http%3A%2F%2F127.0.0.1%3A4200/
#http://127.0.0.1:4200/contest?ope=calvi22
@app.route('/api/get_new_code/<ope>/<url_appli>',methods=["GET"])
@app.route('/api/get_new_code/<ope>',methods=["GET"])
def get_token_for_contest(ope:str,url_appli:str="https://tokenfactory.nfluent.io"):
  """
  Retourne un nouveau NFT
  voir get_new_token, get_new_nft
  :param ope:
  :param url_appli:
  :return:
  """
  format=request.args.get("format","json")

  _opes=open_operation(ope)
  lottery=_opes["lottery"]

  #chargement des NFTs
  nfts=get_nfts_from_src(_opes["data"]["sources"],lottery["collections"],with_attributes=False)
  if len(nfts)==0:
    log("Aucun NFT n'est disponible")
    return "Aucun NFT",404

  # #vérification de la possibilité d'emettre
  # dao=DAO(ope=_opes)
  # if dao.db is None:
  #   rc=dao.db["histo"].aggregate([{"$match":{"command":"mint"}},{"$group":{"_id":"$operation","count": { "$sum": 1 }}}])
  #   for e in rc:
  #     if e["_id"]==_opes["id"]:
  #       if "limits" in lottery and lottery["limits"]["by_year"]<e["count"]:
  #         nfts=[]


  if not "dtStart" in lottery or lottery["dtStart"]=="now":
    nft=None
    for i in range(200):
      nft=nfts[int(random()*len(nfts))]
      if "elrond" in nft.network:
        if nft.owner==nft.creators[0] or Elrond(nft.network).canMint(nft):break

    visual=nft.visual if lottery["screen"]["showVisual"] else ""

    url=str(base64.b64decode(url_appli),"utf8")+"/dm/?"+setParams({
      "toolbar":"false",
      "section":"lottery",
      "address":nft.address,
      "symbol":nft.symbol,
      "ope":_opes["id"]
    })

    buffer=BytesIO()
    pyqrcode.create(url).png(buffer,scale=9)

    if format=="qrcode":
      response = make_response(buffer.getvalue())
      response.headers.set('Content-Type', 'image/png')
      return response

    rc={
      "url":url,
      "visual":visual,
      "qrcode":"data:image/png;base64,"+str(base64.b64encode(buffer.getvalue()),"utf8")
    }
  else:
    rc={"error":"no NFT"}

  return jsonify(rc)






#http://127.0.0.1:4200/dealermachine/?id=symbol2LesGratuits
@app.route('/api/nfts_from_operation/<ope>/',methods=["GET"])
def nfts_from_operation(ope=""):
  _ope=get_operation(ope)
  if _ope:
    nfts=get_nfts_from_src(_ope["data"]["sources"],with_attributes=False)

    sources=[]
    for s in _ope["data"]["sources"]:
      if s["active"]: sources.append(s)

    return jsonify({"total":len(nfts),
                    "nfts":[x.__dict__ for x in nfts],
                    "sources":sources
                    })

  return "No NFT",401



@app.route('/api/mint_from_prestashop/',methods=["POST","GET"])
def mint_for_prestashop():
  body=request.json
  if body is None:return jsonify({"error":"method GET not implemented"})
  log("Réception de "+str(body))

  _p=body["product"]
  mail_content=body["mail_content"] | "mail_new_account"

  log("Chargement de l'opération "+_p["reference"])
  _operation=get_operation(_p["reference"].split(" / ")[0])

  prestashop=PrestaTools(_operation["store"]["prestashop"]["api_key"],_operation["store"]["prestashop"]["server"])
  _p=prestashop.get_products(_p["id_product"])
  _c=prestashop.get_categories(int(_p["associations"]["categories"][0]["id"]))

  _p=prestashop.complete_product_with_features(_p)
  if not "network" in _p:_p["network"]=_operation["lazy_mining"]["network"]

  nft:NFT=prestashop.convert_to_nft(_p)

  collection=_c["name"]
  id_image=_p["associations"]["images"][0]["id"]
  miner=body["miner"] if "miner" in body else _operation["lazy_mining"]["miner"]
  visual=_p["visual"] if "visual" in _p else _operation["store"]["prestashop"]["server"]+"api/images/products/"+id_image+"/"+id_image+"?ws_key="+_operation["store"]["prestashop"]["api_key"]

  addresses=dict()
  if "address" in body and not body["address"] is None:
    addresses=yaml.load(body["address"]) or dict()

  attributes=prestashop.desc_to_dict(_p["description"])

  if "elrond" in _p["network"]:
    elrond=Elrond(_p["network"])
    royalties=body["royalties"] if "royalties" in body else 0

    if not "elrond" in addresses:
      _account,pem,words,qrcode=elrond.create_account(email=body["email"],domain_appli=app.config["DOMAIN_APPLI"],mail_content=mail_content)
      addresses["elrond"]=_account.address.bech32()
      prestashop.edit_customer(body["customer"],"note",yaml.dump(addresses))
      bNewAccount=True
    else:
      _account=elrond.toAccount(addresses["elrond"])
      bNewAccount=False

    if not "address" in _p or _p["address"] is None or _p["address"]=="":
      collection_id,newCollection=elrond.add_collection(miner,collection,type="NonFungible")
      nonce,rc=elrond.mint(miner,_p["name"],_p["description"],collection_id,attributes,IPFS(IPFS_SERVER),[],body["quantity"],royalties,visual)
      t=elrond.transfer(collection_id,nonce,miner,_account)
    else:
      collection_id,nonce=elrond.extract_from_tokenid(_p["address"])
      t=elrond.transfer(collection_id,nonce,_p["owner"],_account)

    account_addr=_account.address.bech32()

    if t is None:
      return returnError("Impossible de transférer le NFT",{"address":_account.address.bech32()})
    else:
      if not bNewAccount:
        send_mail(open_html_file("new_nft",{
          "mini_wallet":"?"+setParams({"toolbar":"false","network":_p["network"],"addr":account_addr}),
        },domain_appli=app.config["DOMAIN_APPLI"]),body["email"],subject="Votre NFT est disponible dans votre wallet")


  if "solana" in _p["network"]:
    solana=Solana(_p["network"])
    if not "solana" in addresses:
      words,pubkey,privkey,integers_private_key=solana.create_account(body["email"],domain_appli=app.config["DOMAIN_APPLI"])
      addresses["solana"]=pubkey
      prestashop.edit_customer(body["customer"],"note",yaml.dump(addresses))
    else:
      pubkey=addresses["solana"]

    if not "address" in _p or len(_p["address"])==0:
      _data=solana.prepare_offchain_data({
        "attributes":attributes,
        "category":"image",
        "properties":{"creators":[{"address":c.split("_")[0],"share":int(c.split("_")[1])} for c in _p["creators"].split(" ")]},
        "seller_fee_basis_points":int(_p["royalties"]) if "royalties" in _p else 0,
        "image":_p["visual"],
        "name":_p["name"],
        "symbol":_p["reference"].split(" / ")[1],
        "description":_p["description"],
        "collection":collection
      })
      rc=solana.mint(_data,miner=miner,sign=True,owner=pubkey)
    else:
      result=solana.transfer(_p["address"],pubkey,_p["owner"])
      if not result:
        return returnError("Probléme de transfert",{"address":pubkey})
    account_addr=pubkey




  return jsonify({"result":"ok","address":account_addr,"mint":nonce})




#http://127.0.0.1:4200/dealermachine/?id=symbol2LesGratuits
@app.route('/api/upload_attributes_file/<config_id>/',methods=["POST"])
def upload_attributes_file(config_id:str):
  txt=str(base64.b64decode(request.data),"utf8")
  attributes=csv.DictReader(StringIO(txt),delimiter="\t")
  nft.attributes=list(attributes)
  return jsonify({"message":"ok"})




#http://127.0.0.1:4200/dealermachine/?id=symbol2LesGratuits
@app.route('/api/mint_for_contest/<confirmation_code>/',methods=["GET"])
@app.route('/api/mint_for_contest/',methods=["POST"])
def mint_for_contest(confirmation_code=""):
  """
  adresse de test : erd1z4pjcxsqag8hy3nwpxwmvmnqt82tanymh8hdzleahqtl9xs0cf4slszcku
  :param confirmation_code:
  :return:
  """
  if request.method=="GET":
    body=json.loads(base64.b64decode(confirmation_code))
  else:
    body=request.json

  #l'id est utile pour retrouver le token afin de mettre a jour sa quantité
  account=body["account"]
  network=body["network"]
  miner=body["miner"] if body["miner"] and len(body["miner"])>0 else body["token"]["collection"]["owner"]
  metadata_storage=body["metadata_storage"]

  _ope=open_operation(body["ope"])
  if _ope is None:
    _data=body["token"]
    if _data["marketplace"]["quantity"]==0: _data=None
  else:
    _data:NFT=None
    nfts=get_nfts_from_src(_ope["data"]["sources"],with_attributes=True)
    for nft in nfts:
      if nft.address==body["token"]["address"] and nft.marketplace["quantity"]>0:
        _data=nft
        break

  if _data is None: return jsonify({"error":"Ce NFT n'est plus disponible"})

  rc=mint(_data,miner,account,network,metadata_storage)

  if len(rc["error"])==0:
    if not _ope is None:
      dao.add_histo(_ope["id"],"mint",account,nft.collection["name"],rc["result"]["transaction"],_ope["network"],"minage pour loterie")

    DAO(_data["domain"],_data["dbname"]).update(_data.__dict__,"quantity")

  return jsonify(rc)



@app.route('/api/apply_filter/',methods=["POST"])
def apply_filter():
  body=request.json
  l=nft.get_layer(body["layer"])
  if l is None: return jsonify({"error":"layer unknonw"})

  rc=l.apply_filter(body["filter"])
  return jsonify({"error":"","images":rc})








@app.route('/api/configs/<location>/',methods=["GET","DELETE"])
@app.route('/api/configs/',methods=["GET","POST"])
#test http://127.0.0.1:4242/api/infos/
#test https://server.f80lab.com:4242/api/infos/
def configs(location:str="",format=""):

  #Utilisé par load_config
  if request.method=="GET" or format=="dict":

    if len(format)==0: format=request.args.get("format","yaml")
    if location.startswith("b64"): location=base64.b64decode(location[3:])

    if location.startswith("http"):
      return jsonify(yaml.load(location,Loader=yaml.FullLoader))

    rc=[]
    for f in os.listdir("./Configs"):
      with open("./Configs/"+f,"r",encoding="utf8") as file:
        config=yaml.load(file,Loader=yaml.FullLoader)
        if not "text" in config:config["text"]={}
        if not "text_to_add" in config["text"]:config["text"]["text_to_add"]=""

        if len(location)==0 or config["name"]==location:
          rc.append(config)

    if format=="json": return jsonify(rc)
    if format=="file" and len(rc)>0:
      filename=rc[0]["location"]
      return send_file(path_or_file="./Configs/"+filename,mimetype="plain/text",as_attachment=True,download_name=filename)

    return rc

  if request.method=="DELETE":
    os.remove("./Configs/"+location)
    return jsonify({"error":"","message":"fichier supprimé"})

  if request.method=="POST":
    s = request.json
    filename="./Configs/"+s["location"]

    #s["attributes"]=nft.attributes
    s=str(yaml.dump(s,default_flow_style=False,indent=4,encoding="utf8"),"utf8")

    log("Ecriture effective du fichier de contenu "+filename)
    f=open(filename,"w",encoding="utf8")
    f.write(s)
    f.close()

    log("Fermeture du fichier")

    return jsonify({"error":"","content":s})




#
# @app.route('/api/ftx/tokens/',methods=["GET"])
# @app.route('/api/ftx/nfts/',methods=["GET"])
# #test http://127.0.0.1:4242/api/ftx/tokens/?key=solMintAddress&value=!none&out=solMintAddress,description,id
# #test https://server.f80lab.com:4242/api/ftx/tokens/?key=solMintAddress&value=!none&out=solMintAddress,description,id
# def ftx_tokens():
#   key=request.args.get("key","solMintAddress")
#   value=request.args.get("value","!none")
#   out=request.args.get("out","")
#   rc=ftx.nfts("nfts",key,value,out,timeout=int(request.args.get("timeout","0")))
#   if rc["status_code"]==200:
#     log(str(len(rc))+" NFTs trouvés")
#
#   return jsonify(rc)



# @app.route('/api/ftx/collections/',methods=["GET"])
# #test http://127.0.0.1:4242/api/ftx/collections/
# #test https://server.f80lab.com:4242/api/ftx_tokens/
# def ftx_collections():
#   filter=request.args.get("filter","")
#   rc=ftx.collections(filter)
#   return jsonify(rc)
#
#
# @app.route('/api/ftx/account/',methods=["GET"])
# #test http://127.0.0.1:4242/api/ftx/account/
# def ftx_account():
#   rc=ftx.account()
#   return jsonify(rc)





@app.route('/api/keys/',methods=["GET"])
@app.route('/api/keys/<name>/',methods=["DELETE","POST"])
#https://metaboss.rs/set.html
#test http://127.0.0.1:4200/api/keys/
#test https://server.f80lab.com:4242/api/keys/
def keys(name:str=""):
  network=request.args.get("network","solana-devnet").lower()

  if request.method=="GET":
    with_balance=(request.args.get("with_balance","false")=="true")
    if "elrond" in network:
      return jsonify(Elrond(network).get_keys(qrcode_scale=int(request.args.get("qrcode_scale","0")),with_balance=with_balance))
    if "solana" in network:
      rc=Solana(network).get_keys(with_private=(request.args.get("with_private","false")=="true"),with_balance=with_balance,with_qrcode=True)
      return jsonify(rc)
    if "polygon" in network:
      rc=Polygon(network).get_keys(3,with_balance=with_balance)
      return jsonify(rc)


  if request.method=="DELETE":
    if "polygon" in network:
      filename=POLYGON_KEY_DIR+name+".secret"
    else:
      filename=(SOLANA_KEY_DIR+name+".json").replace(".json.json",".json") if "solana" in network else (ELROND_KEY_DIR+name+".pem").replace(".pem.pem",".pem")

    os.remove(filename)

  if request.method=="POST":
    obj=request.json

    if "key" in obj:
      key=obj["key"]
      if not key.startswith("["):
        key=str([ord(x) for x in key])
    else:
      email=request.args.get("email","")
      if "solana" in network:
        mnemonic,pubkey,privkey,key=Solana(network).create_account(email,domain_appli=app.config["DOMAIN_APPLI"])
      else:
        _u,key,words,qrcode=Elrond(network).create_account(email,
                                                           network=network,
                                                           domain_appli=app.config["DOMAIN_APPLI"])

    f = open(filename, "w")
    f.write(key)
    f.close()

  return jsonify({"message":"ok"})

#
#
# @app.route('/api/refill/',methods=["GET"])
# #https://metaboss.rs/mint.html
# def refill():
#   addr=request.args.get("addr","")


@app.route('/api/scan/<token>',methods=["GET"])
#http://127.0.0.1:4242/api/scan/HQwsV7o25ZPaDrBLHT7mDs2vbrAUjzujexF2aBkmLHZh
def explorer(token:str):
  network=request.args.get("network","solana-devnet")
  format=request.args.get("format","json")
  rc=Solana(network).scan(token)
  if format=="json":
    return jsonify(rc)
  else:
    return str(rc)




@app.route('/api/use/',methods=["GET"])
#https://metaboss.rs/mint.html
def use():
  keyfile=request.args.get("keyfile","paul")
  network=request.args.get("network","solana-devnet")
  owner=request.args.get("owner")
  account=request.args.get("account","")
  rc=Solana(network).exec("use utilize",param="-h "+owner,account=account,keyfile=keyfile)
  return jsonify(rc)


#https://server.f80lab.com:4242/api/images
#http://localhost:4242/api/images/
@app.route('/api/images/<cid>',methods=["GET","DELETE"])
@app.route('/api/images/',methods=["GET","DELETE"])
def get_image(cid:str=""):
  """
  note: l'upload des images se fait via l'api upload
  :param cid:
  :return:
  """
  if request.method=="GET":
    if len(cid)==0:
      return jsonify({"files":os.listdir("./temp")})
    else:
      filename="./temp/"+cid
      if exists(filename):
        if filename.endswith(".yaml"):
          f=open(filename,"r")
          format="text/yaml"
        else:
          f=open(filename,"r" if cid.endswith(".svg") else "rb")
          if filename.endswith("7z"):
            format="application/zip"
          else:
            format="image/svg+xml" if cid.endswith(".svg") else "image/webp"

        response = make_response(f.read())
        response.headers.set('Content-Type', format)
        return response
      else:
        return returnError("Fichier inexistant",status=404)


  if request.method=="DELETE":
    if "/api/images/" in cid:cid=cid.split("/api/images/")[1].split("?")[0]
    if cid in os.listdir("./temp/"):
      os.remove("./temp/"+cid)
    return "Ok",200


@app.route('/api/json/<cid>',methods=["GET"])
def get_json(cid:str):
  rc=dao.get_dict(cid)
  if rc is None:rc={}
  if "_id" in rc: del rc["_id"]
  return jsonify(rc)



@app.route('/api/sign/',methods=["GET"])
#https://metaboss.rs/mint.html
def sign():
  creator=request.args.get("creator","")
  keyfile=request.args.get("keyfile","paul")
  network=request.args.get("network","solana-devnet")
  account=request.args.get("account","")
  log("Demande de signature pour "+keyfile)
  rc={}
  if len(account)>0:
    rc=Solana(network).exec("sign one",account=account,keyfile=keyfile)
  return jsonify(rc)




#
# @app.route('/api/nft/<owner>/<tokenid>/',methods=["GET"])
# def get_nft(owner:str,tokenid:str):
#   network=request.args.get("network","solana-devnet")
#   if "elrond" in network:
#     nft=Elrond(network).get_nft(owner=owner,token_id=tokenid)
#   return jsonify(nft)
#


#https://server.f80lab.com:4242/api/nfts/
#http://127.0.0.1:4242/api/nfts/
@app.route('/api/nfts/',methods=["GET"])
@app.route('/api/nfts/<id>/',methods=["GET"])
def nfts(id=""):
  network=request.args.get("network","solana-devnet")
  account=request.args.get("account","paul")
  with_attr="with_attr" in request.args
  limit=int(request.args.get("limit","2000"))
  offset=int(request.args.get("offset","0"))

  log("Récupération de "+str(limit)+" nfts sur "+network+" à partir de "+str(offset))

  rc=[]
  if "elrond" in network:
    if id=="":
      l_nfts=Elrond(network).get_nfts(account,limit,with_attr=with_attr,offset=offset,with_collection=True)
    else:
      l_nfts=[Elrond(network).get_nft(token_id=id,attr=True)]
  else:
    l_nfts=Solana(network).get_nfts(account,offset,limit)

  log(str(len(l_nfts))+" NFT identifiés")

  rc=rc+l_nfts
  nfts=[]
  for nft in rc:
    nfts.append(nft.__dict__)

  return jsonify(nfts)




@app.route('/api/access_code_checking/<access_code>/<addr>/',methods=["GET"])
#http://127.0.0.1:4242/api/access_code_checking/
def access_code_checking(access_code:str,addr:str):
  if get_access_code_from_email(addr)==access_code or access_code==SECRET_ACCESS_CODE:
    return jsonify({"message":"ok"})
  else:
    return returnError("Incorrect access code")




@app.route('/api/validate/',methods=["GET"])
#http://127.0.0.1:4242/api/validate/?q=symbol1&ope=calvi2022&network=devnet
def validate():
  rc=dict()

  query=request.args.get("q","")
  operation=request.args.get("ope","").lower()
  network=request.args.get("network","solana-devnet").lower()

  _ope=open_operation(operation)
  if _ope:
    with open("./Operations/"+_ope["data"]) as csvFile:
      data=csv.DictReader(csvFile,delimiter=";")
      for l in list(data):
        if l[_ope["find"]["field"]]==query:
          nft=Solana(network).get_token(l["address"],network)
          if nft[_ope["to_check"]] in _ope["values"]:rc={"validity":"ok"}

  return jsonify(rc)


@app.route('/api/token_by_delegate/',methods=["GET"])
#http://127.0.0.1:4242/api/token_by_delegate/?account=LqCeF9WJWjcoTJqWp1gH9t6eYVg8vnzUCGBpNUzFbNr
def get_token_by_delegate():
  network=request.args.get("network","solana-devnet")
  account=request.args.get("account","")
  rc=Solana(network).get_token_by_miner(account)
  return jsonify(rc)


@app.route('/api/encrypt_key/<name>',methods=["GET"])
#http://127.0.0.1:4242/api/token_by_delegate/?account=LqCeF9WJWjcoTJqWp1gH9t6eYVg8vnzUCGBpNUzFbNr
def encrypt_key(name:str):
  filename=(SOLANA_KEY_DIR+name+".json").replace(".json.json",".json")
  if request.method=="GET":
    f = open(filename, "r")
    s=f.read()
    f.close()

  return jsonify({"encrypt":str(base64.b64encode(encrypt(s)),"utf8")})



@app.route('/api/send_email_to_validateur/',methods=["POST"])
@app.route('/api/send_email_to_validateur/<user>',methods=["POST"])
#http://127.0.0.1:4242/api/token_by_delegate/?account=LqCeF9WJWjcoTJqWp1gH9t6eYVg8vnzUCGBpNUzFbNr
def send_email_to_validateur(user=""):
  operation=request.json
  validate_section=operation["validate"]

  for validateur in validate_section["users"]:
    if len(user)==0 or user==validateur:
      access_code= get_access_code_from_email(validateur)
      url=validate_section["application"]+"&access_code="+access_code+"&ope="+operation["id"]
      url_help=validate_section["support"]["faq"]
      send_mail(open_html_file("mail_validateur",{
        "title":operation["title"],
        "url_appli":url,
        "url_help":url_help,
        "access_code":access_code
      },domain_appli=app.config["DOMAIN_APPLI"]),validateur,subject=operation["title"]+" connexion à l'application de validation")

  return jsonify({"error":""})




@app.route('/api/send_transaction_confirmation/<email>/',methods=["POST"])
def send_transaction_confirmation(email:str):
  body=request.json
  send_mail(open_html_file("transaction_confirmation",{
    "n_passes":body["n_passes"],
    "nft_url":body["nft_url"],
    "nft_title":body["nft_title"]
  },domain_appli=app.config["DOMAIN_APPLI"]),email,subject="Utilisation de votre NFT pour obtenir votre passe")
  return jsonify({"error":""})





@app.route('/api/extract_zip/',methods=["POST"])
def extract_zip():
  pass


@app.route('/api/upload/',methods=["POST"])
def upload():
  """
  Chargement des visuels
  :return:
  """

  platform=request.args.get("platform","ipfs")
  if str(request.data,"utf8").startswith("{"):
    body=request.json
  else:
    content=str(request.data,"utf8")
    if not "base64" in content:content=";base64,"+content
    body={
      "filename":request.args.get("filename"),
      "content":content,
      "type":request.args.get("type","")
    }

  if request.args.get("convert","")!="":
    format=request.args.get("convert","webp")
    buffered=convert_to(body["content"],format=format,quality=95)
    body["content"]="data:image/"+format+";base64,"+str(base64.b64encode(buffered.getvalue()),"utf8")
    body["type"]="image/"+format

  if body["type"]=="":
    if "filename" in body and body["filename"].startswith("qrcode:"):
      body["type"]="image/png"

      qr=pyqrcode.create(body["filename"].split("qrcode:")[1])
      buffered = BytesIO()
      qr.png(buffered,scale=3)

      body["content"]=";base64,"+str(base64.b64encode(buffered.getvalue()),"utf8")
      body["filename"]="qrcode.png"

    else:
      if body["type"]=="":
        if body["filename"].endswith(".mp4") or body["filename"].endswith(".avi") or body["filename"].endswith(".webm"):
          body["type"]="video/"+body["filename"]
        else:
          body["type"]="image/"+body["filename"].split(".")[1]

  if "zip" in body["type"]:
    rc=[]
    b=BytesIO(base64.b64decode(body["content"].split("base64,")[1]))
    with py7zr.SevenZipFile(b, 'r') as zip:
      zip.extractall(".")
      for fname in zip.getnames():
        rc.append(upload_on_platform({
          "filename":fname,
          "type":"image/"+fname[fname.rindex('.')+1:]
        },platform))

  else:
    rc=upload_on_platform(body,platform)

  return jsonify(rc)


#
# @app.route('/api/upload_list/',methods=["POST"])
# def upload_list():
#   mints=request.data
#   with open("account_list.txt", 'w') as f:
#     f.writelines(mints)
#     f.close()
#
#
# @app.route('/api/get_list/',methods=["GET"])
# def get_list():
#   s=""
#   with open("account_list.txt", 'r') as f:
#     s=f.readlines()
#     f.close()
#   return s
#

@app.route('/api/upload_metadata/',methods=["POST"])
def upload_metadata():
  network=request.args.get("network","solana-devnet")

  _data=request.json
  id=request.args.get("filename_for_metadata",None)
  repo=request.args.get("repository","CalviOnTheRocks2022")
  offchaindata_platform=request.args.get("offchaindata_platform","ipfs").replace(" ","").lower()
  if "solana" in network.lower():
    solana=Solana(network)
    rc=upload_on_platform(solana.prepare_offchain_data(_data),offchaindata_platform,id=id,options={"repository":repo})

  return jsonify(rc)


@app.route('/api/create_collection/<owner>/',methods=["POST"])
def create_collection(owner:str):
  _data=request.json
  network=request.args.get("network","elrond-devnet")
  if "elrond" in network:
    elrond=Elrond(network)
    solde=elrond.balance(owner)
    collection_id,newCollection=elrond.add_collection(owner,_data["name"],_data["options"],type="NonFungible")
    if not newCollection:
      return returnError("Cette collection existe déjà")

    new_collection=elrond.get_collection(collection_id)
    new_solde=elrond.balance(owner)

  return jsonify({
    "collection":new_collection,
    "cost":solde-new_solde
  })


def mint(nft:NFT,miner,owner,network,offchaindata_platform="IPFS",storagefile="",wallet_appli="https://wallet.nfluent.io"):
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
  rc= {"error":"Problème technique"}
  account=None
  collection_id=nft.collection["id"] if nft.collection else ""

  if is_email(owner):
    email=owner
    if "elrond" in network:
      elrond=Elrond(network)
      _account,pem,words,qrcode=elrond.create_account(email=email,
                                                      network=network,
                                                      subject="Votre NFT '"+nft.name+"' est disponible",
                                                      domain_appli=app.config["DOMAIN_APPLI"])
      account=_account.address.bech32()
      log("Notification de "+owner+" que son compte "+elrond.getExplorer(account,"account")+" est disponible")

    if "solana" in network:
      solana=Solana(network)
      words,pubkey,privkey,list_int=solana.create_account(domain_appli=app.config["DOMAIN_APPLI"],network=network,subject="Votre NFT '"+nft.name+"' est disponible")
      account=pubkey

    if "polygon" in network:
      words,pubkey,privkey,list_int=Polygon(network).create_account(domain_appli=app.config["DOMAIN_APPLI"],network=network,subject="Votre NFT '"+nft.name+"' est disponible")
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
    nonce,rc=Polygon(network).mint(
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
      visual=nft.visual
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

  if "database" in network.lower():
    db_loc=request.args.get("db_loc","")
    if len(db_loc)==0: db_loc=network.split("-")[1]
    db_name=request.args.get("db_name","")
    if len(db_name)==0: db_name=network.split("-")[2]

    if dao.connect(db_loc,db_name):
      rc=dao.lazy_mint(nft,"",app.config["APPLICATION_ROOT"])


  if "file" in network.lower():
    if not storagefile.startswith("./temp/"): storagefile="./temp/"+storagefile
    storefile=StoreFile(storagefile)
    rc=storefile.lazymint(nft)
    storefile.export_to_yaml()

  # if "jsonfiles" in network.lower():
  #   filename=_data["name"]+"_"+_data["symbol"]+"_"+_data["collection"]+".json"
  #   with open("./temp/"+filename,"w") as f:
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


@app.route('/api/set_role_for_collection/',methods=["POST"])
def set_role_for_collection():
  collection_id=request.json['collection_id']
  owner=request.json['owner']
  network=request.json["network"]
  if "elrond" in network:
    t=Elrond(network).set_roles(collection_id,owner)
    return jsonify({"transaction":t})





@app.route('/api/mint/',methods=["POST"])
def api_mint():
  """
  Minage des NFT sur les différents réseaux possibles : elrond, solana, base de donnée, fichier json
  :return:
  """
  keyfile=request.args.get("keyfile","paul").lower()
  storagefile=request.args.get("storage_file","./temp/storagefile.yaml").lower()
  network=request.args.get("network","elrond-devnet")
  owner=request.args.get("owner",keyfile)
  offchaindata_platform=request.args.get("offchaindata_platform","ipfs").replace(" ","").lower()
  _data=NFT(object=request.json)

  rc=mint(_data,keyfile,owner,network,offchaindata_platform,storagefile)

  if not _data.visual.startswith("http"):
    return jsonify({"error":"Vous devez uploader les images avant le minage"})

  return jsonify(rc)




@app.route('/api/mint_from_file/',methods=["POST"])
#https://metaboss.rs/mint.html
def mint_from_file():
  ipfs=IPFS(IPFS_SERVER,5001)

  keyfile=request.args.get("account","paul")
  sign=request.args.get("sign",False)

  files:FileStorage = request.files.getlist('files')
  _datas=dict()
  for file in files:
    if "image" in file.content_type:
      _datas[file.filename]=ipfs.get_link(ipfs.add_file(file))
    else:
      data=file.stream.readlines()
      content=[str(x,"utf8") for x in data]
      _datas[file.filename]=json.loads("".join(content))

  for k in list(_datas.keys()):
    _data=_datas[k]
    if k.endswith(".json"):
      offchain:dict={"attributes":_data["attributes"]}
      if "files" in _data["properties"]:
        offchain["files"]=_data["properties"]["files"]
        for f in offchain["files"]:
          if "uri" in f and not f["uri"].startswith("http"):
            f["uri"]=_datas[f["uri"]]


      _data["uri"]=ipfs.get_link(ipfs.add(offchain))

      if "properties" in _data:
        _data["creators"]=_data["properties"]["creators"]

      for c in _data["creators"]:
        c["verified"]=(c["verified"]==1)

      for k in ["properties","collection","image","attributes"]:
        if k in _data:del _data[k]

      file_to_mint="./Temp/to_mint"+datetime.datetime.now().timestamp()+".json"
      with open(file_to_mint, 'w') as f:
        f.writelines(json.dumps(_data))
        f.close()

      rc=exec("mint one","--nft-data-file "+file_to_mint+(" --sign" if sign else ""),keyfile=keyfile)
      if len(rc["error"])==0:os.remove(file_to_mint)

  return jsonify({"error":rc["error"],"message":rc["result"]})



# import pandas as pd
#
# @app.route('/api/mint_from_file/<ope>/',methods=["POST"])
# def mint_from_file(ope:str,data:dict=None):
#   if data is None:
#     data = json.loads(str(request.data, encoding="utf-8"))
#
#   if "base64" in data["content"]:
#     data["content"]=str(base64.b64decode(data["content"].split("base64,")[1]),"utf8")
#
#   format=request.args.get("filename","xlsx")
#
#   if format.endswith("xlxs"):
#     df:DataFrame = pd.read_excel(data["content"])
#     rows=df.iterrows()
#     keys=df.iloc[3]
#
#   rc=[]
#   index=0
#   for i in range(3,len(df.iterrows())):
#     token=dict()
#     for j in range(0,len(keys)):
#       k=df.iloc[i][j].split(".")
#
#     if ope=="mint":
#       #Execution du fichier
#       if index in data["to_mint"]:
#         result=mint(row["count"],body)
#         rc=rc+result.json
#     else:
#       #Analyse du fichier
#       rc.append({"count":row["count"],"title":row["title"],"cost":bc.eval_gas(200),"to_mint":row["to_mint"],"index":index})
#
#     index=index+1
#
#
#   return jsonify(rc),200
#
#



@app.route('/api/update_obj/',methods=["POST"])
def update_obj():
  ipfs=IPFS(IPFS_SERVER,5001)
  network=request.args.get("network")
  keyfile=request.args.get("keyfile")
  account=request.args.get("account")

  if "elrond" in network:
    rc=Elrond(network).update(
      user=keyfile,
      token_id=account,
      properties=request.json,
      ipfs=ipfs
    )
    return rc
  else:
    cid=ipfs.add(request.json)
    url=ipfs.get_link(cid["Hash"])
    return Solana(network).exec("update","uri --new-uri "+url,account=account,keyfile=keyfile)


@app.route('/api/export/',methods=["POST"])
def export():
  ipfs=IPFS(IPFS_SERVER,5001)
  i=0
  with ZipFile('./Temp/archive.7z', 'w') as myzip:
    for token in request.json:
      file_to_mint="./Temp/"+str(i)+".json"
      with open(file_to_mint, 'w') as f:
        f.writelines(json.dumps(token,indent=4, sort_keys=True))
        f.close()

      myzip.write(file_to_mint)
      i=i+1

    myzip.close()
  cid=ipfs.add_file('./Temp/archive.7z')
  return jsonify({"zip_file":ipfs.get_link(cid)})





@app.route("/login", methods=["POST"])
def login():
  """
  Create a route to authenticate your users and return JWTs. The
  create_access_token() function is used to actually generate the JWT.
  voir https://flask-jwt-extended.readthedocs.io/en/stable/basic_usage/
  :return:
  """
  username = request.json.get("username", None)
  password = request.json.get("password", None)
  if username != "test" or password != "test":
    return jsonify({"msg": "Bad username or password"}), 401

  access_token = create_access_token(identity=username)
  return jsonify(access_token=access_token)



@app.route('/api/validators/',methods=["GET","POST"])
@app.route('/api/validators/<validator>/',methods=["PUT","GET","DELETE"])
def validators(validator=""):
  if request.method=="GET":
    rc=[]
    log("On demande la liste des validateurs")
    for val in list(dao.db["validators"].find()):
      if len(validator)==0 or validator==val["id"]: #Validator opére comme un filtre
        del val["_id"]
        val["access_code"]=str(base64.b64encode(encrypt(val["id"])),"utf8")
        rc.append(val)
    return jsonify(rc)

  if request.method=="DELETE":
    dao.db["validators"].delete_one({"id":validator})
    return jsonify({"message":"deleted"})

  if request.method=="POST":
    log("Un validateur demande son inscription")
    validator_name="val_"+now("hex") if len(request.json["validator_name"])==0 else request.json["validator_name"]
    access_code=str(base64.b64encode(encrypt(validator_name)),"utf8")
    ask_for:str=request.json["ask_for"]
    dao.add_validator(validator_name,ask_for)

    nfts=[]
    if ask_for.startswith("operation:"):
      operation=open_operation(ask_for.split("operation:")[1])
      elrond=Elrond(operation["network"])
      for nft in get_nfts_from_src(operation["data"]["sources"]):
        if len(operation["validate"]["filters"]["collections"])==0 or nft.collection in operation["validate"]["filters"]["collections"]:
          if not nft.owner: nft=elrond.get_nft(nft.address)
          nfts.append(nft)
      owner=[x.owner for x in nfts]
    else:
      elrond=Elrond(request.json["network"])
      owners=list(set([x["address"] for x in elrond.get_owner_of_collections(ask_for.split(","))]))

    return jsonify({
      "access_code":access_code,
      "id":validator_name,
      "addresses":owners
    })


  if request.method=="PUT":
    rc=dao.db["validators"].update_one({"id":validator},{"$set":request.json})
    return jsonify({"message":"ok"})



@app.route('/api/scan_for_access/',methods=["POST"])
def scan_for_access():
  """
  Validation de la connexion via le nfluent wallet en mode wallet_connect
  Cette api est appelé par le visiteur via la webcam du nfluent wallet
  :return:
  """
  _data=request.json
  if "/api/qrcode/" in _data["validator"]:_data["validator"]=_data["validator"].split("/api/qrcode/")[1]

  validator=decrypt(_data["validator"])
  log("Validateur en charge de la validation : "+validator)
  send(socketio,validator, {"address":_data["address"]})

  log("Ajout de l'adresse "+_data["address"]+" pour validation")
  dao.db["validators"].update_one({"id":validator},{"$set": {"user":_data["address"]}})
  return jsonify({"message":"ok"})





#voir https://metaboss.rs/burn.html
#http://127.0.0.1:9999/api/burn/?account=GwCtQjSZj3CSNRbHVVJ7MqJHcMBGJJ9eHSyxL9X1yAXy&url=
#TODO: ajouter les restrictions d'appel
@app.route('/api/burn/')
def burn():
  account=request.args.get("account")
  keyfile=request.args.get("keyfile")
  delay=request.args.get("delay","1.0")
  network=request.args.get("network","solana-devnet")

  if "elrond" in network:
    rc=Elrond(network).burn(keyfile,account)
  else:
    rc=Solana(network).exec("burn one",account=account,keyfile=keyfile,delay=int(delay))

  return jsonify(rc)



if __name__ == '__main__':

  scheduler.add_job(func=async_mint, trigger="interval", seconds=30,max_instances=1)
  scheduler.start()
  atexit.register(lambda: scheduler.shutdown())

  log("Mise a place du modele CORS")
  CORS(app)


  app.config.from_mapping({
    "DEBUG": True,                    # some Flask specific configs
    "CACHE_TYPE": "SimpleCache",      # Flask-Caching related configs
    "CACHE_DEFAULT_TIMEOUT": 300,
    "APPLICATION_ROOT":sys.argv[2],
    "DOMAIN_APPLI":sys.argv[2],
    "DOMAIN_SERVER":sys.argv[1],
    "UPDLOAD_FOLDER":"./Temp/",
    "JWT_SECRET_KEY":SECRET_JWT_KEY
  })
  jwt = JWTManager(app)

  _port=int(app.config["DOMAIN_SERVER"][app.config["DOMAIN_SERVER"].rindex(":")+1:])

  app.config.update(SESSION_COOKIE_SECURE=True,SESSION_COOKIE_HTTPONLY=True,SESSION_COOKIE_SAMESITE='Lax')
  log("Démarage du server")
  if "ssl" in sys.argv:
    context = ssl.SSLContext(ssl.PROTOCOL_TLSv1_2)
    context.load_cert_chain("/certs/fullchain.pem", "/certs/privkey.pem")
    socketio.run(app,debug=("debug" in sys.argv),port=_port,ssl_context=context,host="0.0.0.0",allow_unsafe_werkzeug=True)
  else:
    socketio.run(app,port=_port,host="0.0.0.0",debug=("debug" in sys.argv),allow_unsafe_werkzeug=True)









