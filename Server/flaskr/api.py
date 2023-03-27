import base64
import csv
import datetime
import json
import os
import pickle
import urllib
import urllib.parse
from asyncio import sleep
from copy import copy
from io import BytesIO, StringIO
from os import listdir
from os.path import exists
from random import random
from shutil import copyfile
from zipfile import ZipFile

import py7zr
import pyqrcode
import requests
import yaml
from PIL.Image import Image
from bson import ObjectId
from flask import request, jsonify, send_file, make_response, Blueprint, current_app
from flask_jwt_extended import create_access_token
from werkzeug.datastructures import FileStorage
from yaml import dump, Dumper

import config
from flaskr import Keys
from flaskr.ArtEngine import Layer, Sticker, ArtEngine
from flaskr.Elrond import Elrond, ELROND_KEY_DIR
from flaskr.GitHubStorage import GithubStorage
from flaskr.Keys import Key
from flaskr.Mintpool import Mintpool
from flaskr.NFT import NFT
from flaskr.Network import Network
from flaskr.Polygon import POLYGON_KEY_DIR
from flaskr.PrestaTools import PrestaTools
# from flaskr.Solana import SOLANA_KEY_DIR, Solana
from flaskr.StoreFile import StoreFile
from flaskr.TokenForge import upload_on_platform
from flaskr.Tools import get_operation, decrypt, get_access_code_from_email, send, convert_to, returnError, setParams, \
  get_access_code, check_access_code, get_fonts, log, now, send_mail, open_html_file, encrypt, importer_file, \
  idx, generate_svg_from_fields, get_filename_from_content, queryPixabay, queryUnsplash, isLocal, is_email
from flaskr.TransactionsGraph import TransactionsGraph
from flaskr.apptools import get_network_instance, get_nfts_from_src, mint, transfer, extract_keys_from_operation, \
  get_network_from_address, create_account
from flaskr.dao import DAO
from flaskr.ipfs import IPFS
from flaskr.secret import GITHUB_TOKEN, GITHUB_ACCOUNT, PERMS, SECRETS_FILE, SECRET_ACCESS_CODE, ADMIN_EMAIL, \
  ADMIN_PERMS
from flaskr.settings import IPFS_SERVER, OPERATIONS_DIR, CONFIG_DIR

bp=Blueprint("api",__name__,url_prefix="/api")

#http://127.0.0.1:9999/api/update/?account=GwCtQjSZj3CSNRbHVVJ7MqJHcMBGJJ9eHSyxL9X1yAXy&url=
#TODO: ajouter les restrictions d'appel
@bp.route('/update/')
#https://metaboss.rs/set.html
def update():
  url=request.args.get("url")
  account=request.args.get("account")
  return exec("update","uri --new-uri "+url,account=account)


@bp.route('/palettes/',methods=["GET"])
def get_palettes():
  palette=json.load(open("./palettes.json","r"))
  return jsonify(palette)



@bp.route('/upload_batch/',methods=["POST"])
#http://127.0.0.1:4242/api/upload_batch/
def api_upload_batch():
  data=request.json["content"]
  rows,n_rows=importer_file(data)
  header = [x.lower().strip() for x in rows[0]]
  default_collection="NFLUENTA-af9ddf"
  default_creator="nfluent"

  rc=[]
  for row in rows[1:]:
    nft:NFT=NFT(
      miner=idx("miner",row,"monnft",header=header),
      name=idx("titre,title,name,nom",row,"monnft",header=header),
      visual=idx("visual,visuel,image,photo",row,"",header=header),
      description=idx("desc,description,commentaire",row,"",header=header),
      creators=[idx("creator,createur,createurs,creators",row,default_creator,header=header)],
      collection=idx("collection",row,default_collection,header=header),
      tags=idx("tag,tags",row,"",header=header),
      symbol=idx("symbol,id,identifiant",row,"",header=header),
      marketplace={"price":idx("price,prix,tarif",row,0,header=header),"quantity":idx("quantity,quantité,nombre",row,1,header=header)},
      royalties=idx("royalties,percent,part",row,0,header=header),
      attributes=idx("attributs,attributes,propriétés,properties,property",row,{},header=header)
    )
    rc.append(nft.__dict__)

  return jsonify(rc)




@bp.route('/getyaml/<name>/')
@bp.route('/getyaml/<name>/<format>/')
#http://127.0.0.1:4242/api/getyaml/calvi22/txt/?dir=Operations
def getyaml(name:str,format=None):
  dir=request.args.get("dir",current_app.config["STATIC_FOLDER"])
  dir=dir+("" if dir.endswith("/") else "/")
  if format is None: format=request.args.get("format","json")

  if name.startswith("b64:"):name=str(base64.b64decode(name[4:]),"utf8")
  if name.startswith("http"):
    try:
      _d=yaml.load(requests.get(name).text,Loader=yaml.FullLoader)
      return jsonify(_d)
    except:
      return returnError("La syntaxe du fichier "+name+" est incorrecte")


  filename=dir+name+(".yaml" if not name.endswith(".yaml") else "")
  if not exists(filename): return returnError("Fichier "+filename+" introuvable")

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



@bp.route('/perms/<addr>/',methods=["GET"])
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








@bp.route('/clone_with_color/',methods=["POST"])
def clone_with_color():
  body=request.json
  ae=ArtEngine()
  l=ae.get_layer(body["layer"]["name"])
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







@bp.route('/reset_collection/',methods=["GET"])
#test http://127.0.0.1:4242/api/test/
def reset_collection():
  ArtEngine().reset()
  return jsonify({"status":200})


@bp.route('/fonts/',methods=["GET"])
#test http://127.0.0.1:4242/api/fonts/
def api_get_fonts():
  return jsonify({"fonts":get_fonts()})



@bp.route('/layers/',methods=["POST"])
def layers(body=None):
  """
  charge les couches dans l'instance partagé nft
  :tags: add_layer
  :param body:
  :return:
  """
  nft=ArtEngine()
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
              indexed=(body["indexed"] if "indexed" in body else True),
              scale=body["scale"] if "scale" in body else "1,1",
              translation=body["translation"] if "translation" in body else "0,0",
              margin=body["margin"] if "margin" in body else "0,0"
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
                  fontstyle=elt["text"]["fontstyle"],work_dir=current_app.config["UPLOAD_FOLDER"])
      else:
        if elt["image"] and len(elt["image"])>0:
          if not elt["image"].startswith("data:"):
            ext=elt["image"].split("?")[1] if "?" in elt["image"] else elt["image"][elt["image"].rindex(".")+1:]
            if "/" in elt["image"]:
              name=elt["image"][elt["image"].rindex("/")+1:].split("_0x")[0]
            else:
              name=elt["image"]
          else:
            ext="image/webp"
            name=now("hex")

          s=Sticker(name=name,image=elt["image"],ext=ext,work_dir=current_app.config["UPLOAD_FOLDER"],
                    dimension=(body["width"] if "width" in body else 500,body["height"] if "height" in body else 500))

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




@bp.route('/generate_svg/',methods=["POST"])
def generate_svg():
  """
  :return:
  """
  _data=request.json
  master=Sticker(image=_data["file"],ext="svg",work_dir=current_app.config["UPLOAD_FOLDER"])
  rc=generate_svg_from_fields(master.text["text"])

  return jsonify(rc)


@bp.route('/collections/<addresses>/')
#test http://127.0.0.1:4242/api/collection/herve
def api_get_collections(addresses:str):
  """
  retourne l'ensemble des collections appartenant à un utilisateur
  :return:
  """
  bl=get_network_instance(request.args.get("network","elrond-devnet"))
  detail=(request.args.get("detail","true")=="true")
  operations=request.args.get("operations","canCreate")

  cols=[]
  for addr in addresses.split(","):
    filter_type=request.args.get("filter_type","")
    cols=cols+bl.get_collections(addr, detail=detail, type_collection=filter_type,special_role=operations)

  return jsonify(cols)




@bp.route('/collection/',methods=["GET","POST"])
def get_collection(limit=100,format=None,seed=0,size=(500,500),quality=100,data={},ext="webp"):
  """
  Generation de la collection des NFTs
  tag #generate generate_nft get_collection
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
    nft=ArtEngine(name=request.args.get("name","mycollection").replace(".png",""),
                  work_dir=current_app.config["UPLOAD_FOLDER"])
    target_platform=request.args.get("platform","")

  config=request.json if request.method=="POST" else None

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
  work_dir=current_app.config["UPLOAD_FOLDER"]

  prefix="gen_"+now("random").replace("0x","")
  files=nft.generate(
    dir=work_dir,
    limit=min(limit,max_item),
    seed_generator=seed,
    width=int(size[0]),
    height=int(size[1]),
    quality=quality,
    data=s_data,
    ext=ext,
    attributes=json.loads(urllib.parse.unquote(str(base64.b64decode(attributes), "utf8"))) if len(attributes)>0 else [],
    prefix=prefix,
    target_platform=target_platform if format=="upload" else "",
    domain_server=current_app.config["DOMAIN_SERVER"]
  )

  if format.startswith("zip"):
    email=format.replace("zip_","")

    #Ajout d'un fichier README d'explication à l'archive
    copyfile(current_app.config["STATIC_FOLDER"]+"README_forzipcollection","./README")
    files.append("./README")

    #Ajout du fichier de configuration
    if config:
      config_filename=current_app.config["UPLOAD_FOLDER"]+"config.yaml"
      with open(config_filename,"w") as f:
        f.writelines([
          "#Ceci est le fichier de configuration correspondant à la collection jointe",
          "#Il peut être utilisé dans {{appname}} pour regénérer cette collection",
        ])
        yaml.dump(config,f,Dumper=Dumper)
        files.append(config_filename)
        f.close()

    filename="col_"+now("hex")+".zip"
    archive_file=open(current_app.config["UPLOAD_FOLDER"]+filename,"wb") if is_email(email) else BytesIO()
    with py7zr.SevenZipFile(archive_file, 'w') as archive:
      for f in files:
        archive.write(f)
        os.remove(f)

    if is_email(email):
      archive_file.close()
      url_file=current_app.config["DOMAIN_SERVER"]+"/api/files/"+filename
      send_mail(open_html_file("mail_nft_collection",{"url_collection":url_file}),email,subject="Votre collection")
      return jsonify({"message":"mail contenant la collection envoyé a "+email})
    else:
      archive_file.seek(0)
      return send_file(archive_file,as_attachment=True,download_name="collection.7z")

  else:
    archive_file=""

  # for f in os.listdir(current_app.config["UPLOAD_FOLDER"]):
  #   try:
  #     if f.startswith(prefix):os.remove(work_dir+f)
  #   except:
  #     log("Impossible de supprimer "+f)


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


  if format=="preview" or format=="upload":
    for filename in files:
      f=open(filename,"rb")
      only_filename=filename[filename.rindex("/")+1:]
      rc.append({"src":"data:image/webp;base64,"+str(base64.b64encode(f.read()),"utf8"),"filename":only_filename})
      f.close()
      os.remove(filename)


    return jsonify({"preview":rc,"archive":archive_file})

  return jsonify({"error":"problème technique"})



@bp.route('/send_photo_for_nftlive/<conf_id>/',methods=['POST'])
@bp.route('/send_photo_for_nftlive/',methods=['POST'])
def send_photo_for_nftlive(conf_id:str=""):

  if len(conf_id)==0: conf_id=request.json["config"]
  config=configs(conf_id,format="dict")
  if len(config)==0:
    return returnError("Configuration "+conf_id+" introuvable")
  else:
    config=config[0]

  image=request.json["photo"]
  dim=request.json["dimensions"] if "dimensions" in request.json else str(config["width"])+"x"+str(config["height"])
  if not "x" in dim: dim=dim+"x"+dim
  limit=request.json["limit"] if "limit" in request.json else config["limit"]
  quality=request.json["quality"] if "quality" in request.json else 90
  data=config["data"] if "data" in config else {}
  seq=request.json["sequence"] if "sequence" in request.json else []
  format=request.json["format"]

  dyna_fields=dict()
  for field in request.json["dynamic_fields"] if "dynamic_fields" in request.json else []:
    dyna_fields[field["name"]]=field["value"]

  nft=ArtEngine()
  nft.reset()
  nft.add(Layer("maphoto",position=0))
  nft.add_image_to_layer("maphoto",image)
  for layer in config["layers"]: layers(layer)

  dir=current_app.config["UPLOAD_FOLDER"]

  files=nft.generate(
    dir=dir,
    limit=int(limit),
    seed_generator=0,
    width=int(dim.split("x")[0]),
    height=int(dim.split("x")[1]),
    quality=quality,
    data=data,
    ext="webp",
    replacements=dyna_fields
  )
  if format=="link":
    files=[current_app.config["DOMAIN_SERVER"]+x.replace(dir,"") for x in files]
  else:
    files=[Sticker(image=x).toBase64() for x in files]

  return jsonify({"images":files})







@bp.route('/nftlive_access/<addr>/')
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


@bp.route('/appli_configs/')
def appli_configs():
  """
  retourne la liste des configurations serveur disponibles
  :return:
  """
  rc=[]
  rc.append(config.localConfig.__dict__)
  rc.append(config.Config.__dict__)
  rc.append(config.prodConfig.__dict__)
  return jsonify(rc)







@bp.route('/infos/')
#test http://127.0.0.1:4242/api/infos/
#test http://75.119.159.46:4242/api/infos/
#test https://server.f80lab.com:4242/api/infos/
#test https://api.nfluent.io:4242/api/infos/
def infos():
  dao=DAO(config=current_app.config)
  rc={
    "Server":current_app.config["DOMAIN_SERVER"],
    "Client":current_app.config["DOMAIN_APPLI"],
    "Database_Server":current_app.config["DB_SERVER"],
    "Database_Name":current_app.config["DB_NAME"],
    "Upload_Folder":current_app.config["UPLOAD_FOLDER"],
    "Activity_Report":current_app.config["ACTIVITY_REPORT"],
    "Static_Folder":current_app.config["STATIC_FOLDER"],
    "Menu":current_app.config["MENU"],
    "Database":{
      "tokens":dao.db["nfts"].count_documents(filter={}),
      "validators":dao.db["validators"].count_documents(filter={}),
      "mintpool":dao.db["mintpool"].count_documents(filter={})
      },
    "PLATFORMS":current_app.config["PLATFORMS"],
    "NETWORKS":current_app.config["NETWORKS"]
    }
  return jsonify(rc)





@bp.route('/get_nft_from_db/',methods=["GET"])
def get_nft_from_db():
  dao=DAO(config=current_app.config)
  id=request.args.get("id")
  if id is None: return returnError("id ne peut être nul")
  return jsonify(dao.get(id))



@bp.route('/test/',methods=["GET"])
#http://127.0.0.1:4242/api/test
def test():
  pass



@bp.route('/analyse_transaction/<address>/',methods=["GET"])
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
    tokens=dict()
    for t in elrond.transactions:
      if t["token"]!="" and not t["token"] in tokens: tokens[t["token"]]=elrond.get_nft(t["token"]).toJson()
      t["from"]="factory" if ["method"]=="ESDTNFTCreate" else elrond.find_alias(t["from"],keys)
      t["to"]=elrond.find_alias(t["to"],keys)

    G.load(elrond.transactions,tokens=tokens)

  return jsonify({"graph":G.export()})





@bp.route('/analyse_prestashop_orders/',methods=["GET"])
#test http://127.0.0.1:4242/api/analyse_prestashop_orders/?ope=main_devnet
def analyse_prestashop_orders():
  _operation=get_operation(request.args.get("ope"))
  _store_section=_operation["store"]
  prestashop=PrestaTools(_store_section["prestashop"]["api_key"],_store_section["prestashop"]["server"],_store_section["prestashop"]["language"])
  nfts=prestashop.analyse_order()
  for nft in nfts:
    new_owner=nft.other["owner"]
    mail_new_wallet=_operation["new_account"]["mail"]
    mail_existing_wallet=_operation["transfer"]["mail"]
    #TODO ajouter ici la création de compte

    mint(nft,nft.other["miner"] if "miner" in nft.other else "",new_owner,nft.network)
    prestashop.update_order_status(nft.other["order_id"],4) #Passage de la commande au statut expédié

  return jsonify({"message":"traitement terminé"})


@bp.route('/export_to_prestashop/',methods=["GET",'POST'])
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
        log("La catégorie "+nft.collection["id"]+" n'existe pas dans prestashop. On la créé")
        c=prestashop.add_category(
          ref_col["name"],
          root_category["id"],
          ref_col["description"]
        )
      else:
        log("La catégorie "+nft.collection["id"]+" est bien présente dans prestashop")

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
        return returnError("Impossible de créer "+str(nft))
      else:
        prestashop.set_product_quantity(product,nft.get_quantity())
        filename=current_app.config["UPLOAD_FOLDER"]+"image"+now("hex")+".gif"
        try:
          #buf_image=convert_to_gif(nft.visual,filename=filename)
          sleep(3)
        except:
          log("Impossible de convertire l'image")

        prestashop.add_image(product["id"],filename,work_dir=current_app.config["UPLOAD_FOLDER"])
        os.remove(filename)

  return jsonify({"message":"ok"})





@bp.route('/send_conf/',methods=["POST"])
#test http://127.0.0.1:4242/api/send_conf/
def send_conf():
  data=request.json
  #TODO: envoie de l'email de confirmation à coder
  return jsonify({"error":""})






@bp.route('/tables/<table>',methods=["GET","DELETE"])
#test http://127.0.0.1:4242/api/tables/nfts
def tables(table:str):
  rc=[]
  if request.method=="GET":
    try:
      rows=DAO(config=current_app.config).db[table].find()
    except:
      return jsonify([])


    for row in rows:
      del row["_id"]
      for exclude in request.args.get("excludes","").split(","):
        if len(exclude)>0 and exclude in row: del row[exclude]
      for k in row.keys():
        if type(row[k])==dict or type(row[k])==bytes:
          row[k]=str(row[k])

      rc.append(row)

  if request.method=="DELETE":
    DAO(config=current_app.config).db[table].drop()
    rc={"error":""}

  return jsonify(rc)



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




@bp.route('/change_password/<email>/<access_code>/<new_access_code>/',methods=["GET"])
def api_update_access_code(email:str,access_code:str,new_access_code:str):
  rc=DAO(config=current_app.config).set_access_code(email,access_code,new_access_code)
  if rc:
    send_mail(open_html_file("mail_registration",{"tokenforge_url":current_app.config["DOMAIN_APPLI"],"access_code":new_access_code}),_to=email,subject="Inscription à tokenforge")
    return jsonify({"message":"Mot de passe modifié","error":""})
  else:
    return jsonify({"message":"Mot de passe non modifié","error":"ko"})



@bp.route('/transfer/',methods=["POST"])
def transfer_to():

  nft_addr=request.json["token_id"]
  to=request.json["dest"]
  owner=Key(obj=request.json["from_miner"])
  target_miner=Key(obj=request.json["target_miner"])

  from_network=request.args.get("from_network","elrond-devnet")
  to_network=request.args.get("to_network","elrond-devnet")
  _ope=get_operation(request.args.get("operation",""))

  rc=transfer(addr=nft_addr,from_network_miner=owner,target_network_owner=to,from_network=from_network,target_network=to_network,target_network_miner=target_miner)

  #Création des comptes
  # if "solana" in to_network:
  #   solana=Solana(to_network)
  #   if "@" in to:
  #     words,to,secret_key,secret_key_ints=solana.create_account(to,domain_appli=current_app.config["DOMAIN_APPLI"],network=to_network)
  #   if nft_addr.startswith("db_"): rc=solana.mint({},owner,True,to)
  #   rc=solana.transfer(nft_addr,to,owner)
  #
  # if "elrond" in to_network:
  #   elrond=Elrond(to_network)
  #   if nft_addr.startswith("db_"):
  #     _nft=DAO(network=from_network).get_nft(nft_addr)
  #     t=mint(_nft,owner,to,to_network)
  #     if len(t["error"])>0: return returnError("Probleme de transfert")
  #     token_id=t["result"]["mint"]
  #   else:
  #     collection_id,nonce=elrond.extract_from_tokenid(nft_addr)
  #     if "@" in to:
  #       to,pem,words,qrcode=elrond.create_account(to,
  #                                                 domain_appli=current_app.config["DOMAIN_APPLI"],
  #                                                 mail_new_wallet=_ope["new_account"]["mail"] if not _ope is None else "",
  #                                                 mail_existing_wallet=_ope["transfer"]["mail"] if not _ope is None else "",
  #                                                 histo=DAO(ope=_ope)
  #                                                 )
  #
  #     t=elrond.transfer(collection_id,nonce,elrond.toAccount(owner),to)
  #     token_id=collection_id+"-"+nonce
  #     send(current_app,"nfwallet_"+to,{"action":"refresh"})
  #
  #   nfluent_wallet=elrond.nfluent_wallet_url(to,to_network)
  #   rc=(not t is None)
  #
  # if "polygon" in to_network or "polygon" in from_network:
  #   raise NotImplementedError()

  if rc:
    nfluent_wallet=current_app.config["DOMAIN_WALLET"]
    token_id=rc["result"]["mint"]
    return jsonify({"error":"","message":"NFT transféré","nfluent_wallet":nfluent_wallet,"token_id":token_id})
  else:
    return returnError("Probleme de transfert")


@bp.route('/action_calvi/',methods=["POST"])
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
            rc=upload_on_platform(body["offchain"],
                                  section_method["storage"],
                                  id,{"repository":section_method["repository"]},
                                  upload_dir=current_app.config["UPLOAD_FOLDER"])
            #TODO: Ajouter la destruction de l'ancien fichier
            #private_key=decrypt(operation["accounts"][operation["network"].split("-")[0]][section_method["update_authority"]])
            keyfile=section_method["update_authority"]
            # tx=Solana(operation["network"]).exec("update","uri --new-uri "+rc["url"],account=body["token"],keyfile=keyfile)
          else:
            keyfile=section_method["update_authority"]
            body["offchain"]["attributes"]=attrs
            tx=Elrond(body["network"]).update(keyfile,body["token"],body["offchain"],IPFS(IPFS_SERVER))

          tx_log=tx["error"] if len(tx["error"])>0 else tx["result"]["transaction"]

          DAO(config=current_app.config).add_histo(
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
            rc=GithubStorage(section_method["repository"],"main",GITHUB_ACCOUNT,GITHUB_TOKEN).add(body["offchain"],body["uri"],True)
            DAO(config=current_app.config).add_histo(operation["id"],
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


def analyse_operation(ope):
  """
  Analyse l'opération pour remonter d'éventuelle incoherence dans le message warning
  """
  log("Analyse de "+ope["title"])
  ope["warning"]=""
  if "lazy_mining" in ope:
    for section in ope["lazy_mining"]["networks"]:
      bl=get_network_instance(section["network"])
      account=bl.get_account(section["miner"]) if "miner" in section else None
      if account is None:
        warning="Mineur non identifié"
      else:
        if account.balance<0.1: ope["warning"]="Balance du miner très faible"

  return ope


@bp.route('/operations/',methods=["GET","POST"])
@bp.route('/operations/<ope>/',methods=["DELETE","GET"])
#test http://127.0.0.1:4242/api/operations/
#test http://127.0.0.1:4242/api/operations/calvi22
def manage_operations(ope=""):
  user=request.args.get("user")
  format=request.args.get("format","json")
  if request.method=="GET":
    if len(request.args.get("ope",""))>0: ope=request.args.get("ope")
    if len(ope)>0:
      rc,text_version=get_operation(ope.strip(),with_comment=True)
      rc=analyse_operation(rc)
    else:
      rc=[]
      for o in os.listdir(OPERATIONS_DIR):
        if o.endswith("yaml"):
          log("Chargement de "+o)
          _opes,text_ope=get_operation(o,with_comment=True)
          _opes=analyse_operation(_opes)

          _opes["label"]=_opes["title"]
          _opes["value"]=_opes["id"]

          log("Opération conforme")
          rc.append({"value":_opes,"text":text_ope,"filename":o})

        # if ope.lower()==_opes["id"].lower():
        #   rc=_opes
        #   break

  if request.method=="POST":
    body=str(base64.b64decode(request.json["file"].split("base64,")[1]),"utf8") if request.json["file"].startswith("data:") else request.json["file"]
    if user:
      added=DAO(config=current_app.config).add_doc(doc=body,type_doc="operation",id_doc=body["id"])
    else:
      with open(OPERATIONS_DIR+request.json["filename"],"w",encoding="utf8") as file:
        file.write(body)
      added=True
    rc={"error":"" if added else "Impossible d'ajouter l'opération"}

  if request.method=="DELETE":
    if user is None:
      os.remove(OPERATIONS_DIR+ope)
    else:
      DAO(config=current_app.config).del_doc(id_doc=ope,user=user,type_doc="operation")
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





@bp.route('/save_privacy/',methods=["POST"])
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



@bp.route('/get_tokens_to_send/<ope>/',methods=["GET"])
#test http://127.0.0.1:4242/api/get_tokens_for_dispenser/calvi22_devnet?limit=10
def get_tokens_to_send(ope:str):
  section=request.args.get("section","dispenser")
  _opes=open_operation(ope)
  if _opes is None:return jsonify({"error":"operation unknown"})

  limit=int(request.args.get("limit","100000"))
  nfts=get_nfts_from_src(_opes["data"]["sources"],_opes[section]["collections"])
  nfts=nfts[:limit]

  return jsonify([nft.__dict__ for nft in nfts])




@bp.route('/key/<code>',methods=["GET"])
@bp.route('/qrcode/',methods=["GET"])
@bp.route('/qrcode/<code>',methods=["GET"])
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



@bp.route('/check_access_code/<code>',methods=["GET"])
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


@bp.route('/mintpool/',methods=["GET","DELETE"])
@bp.route('/minerpool/',methods=["GET","DELETE"])
@bp.route('/minerpool/<id>/',methods=["DELETE","POST"])
# http://127.0.0.1:4242/api/minerpool/
def api_minerpool(id=""):
  """
  retourne le contenu de la pool de minage pour les NFTs obtenus via la dealermachine
  :param id:
  :return:
  """
  mintpool=Mintpool(config=current_app.config)
  asks=mintpool.get_mintpool()

  rc=[]
  if request.method=="POST":
    rc={"updated":mintpool.edit_pool(ObjectId(id),None,"")}

  if request.method=="GET":
    for ask in list(asks):
      ask["id"]=str(ask["_id"])
      del ask["_id"]
      rc.append(ask)

  if request.method=="DELETE":
    if len(id)>0:
      if mintpool.delete(id): rc={"message":"ok"}
    else:
      mintpool.reset_mintpool()
      rc={"deleted":"all"}

  return jsonify(rc)



# http://127.0.0.1:4242/api/async_mint/3/
@bp.route('/async_mint/<nbr_items>/',methods=["GET"])
def api_async_mint(nbr_items:str="3"):
  mintpool=Mintpool(config=current_app.config)
  rc=mintpool.async_mint(nbr_items=int(nbr_items),filter=request.args.get("filter",""))
  return jsonify({"message":"ok","n_treated_ask":rc})


@bp.route('/add_task_to_mintpool/',methods=["POST"])
def add_user_for_nft():
  """
  Insere une demande de minage ou transfert d'un NFT d'une collection
  :return:
  """
  mintpool=Mintpool(config=current_app.config)


  _ope:dict=request.json["operation"] if "operation" in request.json else None
  sources=_ope["data"]["sources"] if _ope is not None else request.json["sources"]

  # if _ope and "lazy_mining" in _ope:
  #   #On determine le miner en fonction du réseau sélectionné
  #   for n in _ope["lazy_mining"]["networks"]:
  #     if n["network"]==network:
  #       target_collection=n["collection"] if "collection" in n else None
  #       miner=n["miner"] if "miner" in n else None

  id=mintpool.add_ask(
                      sources=request.json["sources"],
                      target=request.json["target"],
                      wallet=request.json["wallet"],
                      operation="" if _ope is None else _ope["id"]
  )
  if not id is None: send(current_app,"mintpool_refresh")

  return jsonify({"message":"ok","ask_id":id})



@bp.route('/access_code/<addr>',methods=["GET"])
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
        "access_code":str(access_code,'utf-8') if type(access_code)==bytes else access_code
      })







#test http://127.0.0.1:4242/api/get_new_code/demo?format=qrcode
#http://127.0.0.1:4242/api/get_new_code/demo/http%3A%2F%2F127.0.0.1%3A4200/
#http://127.0.0.1:4200/contest?ope=calvi22
@bp.route('/get_new_code/<ope>/<url_appli>',methods=["GET"])
@bp.route('/get_new_code/<ope>',methods=["GET"])
def get_token_for_contest(ope:str,url_appli:str="https://tokenforge.nfluent.io"):
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
@bp.route('/nfts_from_collection/<collection_id>/',methods=["GET"])
def nfts_from_collection(collection_id):
  network=request.args.get("network","elrond-devnet")
  with_attr=(request.args.get("with_attr","false")=="true")
  nfts=get_network_instance(network).get_nfts_from_collections([collection_id],with_attr=with_attr,format="json")
  return jsonify({"nfts":nfts})




#http://127.0.0.1:4200/dealermachine/?id=symbol2LesGratuits
@bp.route('/nfts_from_operation/<ope>/',methods=["GET"])
def nfts_from_operation(ope=""):
  _ope=get_operation(ope)
  if _ope:
    try:
      nfts=get_nfts_from_src(_ope["data"]["sources"],with_attributes=False)
    except Exception as inst:
      return returnError(inst.args)

    sources=[]
    for s in _ope["data"]["sources"]:
      if s["active"]: sources.append(s)

    return jsonify({"total":len(nfts),
                    "nfts":[x.__dict__ for x in nfts],
                    "sources":sources
                    })

  return "No NFT",401



@bp.route('/mint_from_prestashop/',methods=["POST","GET"])
def mint_for_prestashop():
  dao=DAO(config=current_app.config)
  body=request.json
  storage_platform=request.get("storage_platform","nftstorage")
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
      _account,pem,words,qrcode=elrond.create_account(email=body["email"],domain_appli=current_app.config["DOMAIN_APPLI"],mail_content=mail_content,histo=dao)
      addresses["elrond"]=_account.address.bech32()
      prestashop.edit_customer(body["customer"],"note",yaml.dump(addresses))
      bNewAccount=True
    else:
      _account=elrond.toAccount(addresses["elrond"])
      bNewAccount=False

    if not "address" in _p or _p["address"] is None or _p["address"]=="":
      collection_id=elrond.add_collection(miner,collection,type="NonFungible")
      nonce,rc=elrond.mint(miner,_p["name"],_p["description"],collection_id,attributes,storage_platform,[],body["quantity"],royalties,visual)
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
        },domain_appli=current_app.config["DOMAIN_APPLI"]),body["email"],subject="Votre NFT est disponible dans votre wallet")


  # if "solana" in _p["network"]:
  #   solana=Solana(_p["network"])
  #   if not "solana" in addresses:
  #     pubkey,privkey,words,qrcode=solana.create_account(body["email"],domain_appli=current_app.config["DOMAIN_APPLI"])
  #     addresses["solana"]=pubkey
  #     prestashop.edit_customer(body["customer"],"note",yaml.dump(addresses))
  #   else:
  #     pubkey=addresses["solana"]
  #
  #   if not "address" in _p or len(_p["address"])==0:
  #     _data=solana.prepare_offchain_data({
  #       "attributes":attributes,
  #       "category":"image",
  #       "properties":{"creators":[{"address":c.split("_")[0],"share":int(c.split("_")[1])} for c in _p["creators"].split(" ")]},
  #       "seller_fee_basis_points":int(_p["royalties"]) if "royalties" in _p else 0,
  #       "image":_p["visual"],
  #       "name":_p["name"],
  #       "symbol":_p["reference"].split(" / ")[1],
  #       "description":_p["description"],
  #       "collection":collection
  #     })
  #     rc=solana.mint(_data,miner=miner,sign=True,owner=pubkey)
  #   else:
  #     result=solana.transfer(_p["address"],pubkey,_p["owner"])
  #     if not result:
  #       return returnError("Probléme de transfert",{"address":pubkey})
  #   account_addr=pubkey


  return jsonify({"result":"ok","address":account_addr,"mint":nonce})




#http://127.0.0.1:4200/dealermachine/?id=symbol2LesGratuits
@bp.route('/upload_attributes_file/',methods=["POST"])
def upload_attributes_file():
  txt=str(base64.b64decode(request.data),"utf8")
  attributes=csv.DictReader(StringIO(txt),delimiter="\t")
  ArtEngine().attributes=list(attributes)
  return jsonify({"message":"ok"})




#http://127.0.0.1:4200/dealermachine/?id=symbol2LesGratuits
@bp.route('/mint_for_contest/<confirmation_code>/',methods=["GET"])
@bp.route('/mint_for_contest/',methods=["POST"])
def mint_for_contest(confirmation_code=""):
  """
  adresse de test : erd1z4pjcxsqag8hy3nwpxwmvmnqt82tanymh8hdzleahqtl9xs0cf4slszcku
  :param confirmation_code:
  :return:
  """
  dao=DAO(config=current_app.config)
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
  mail_new_wallet=_ope["new_account"]["mail"]
  mail_existing_wallet=_ope["transfer"]["mail"]

  rc=mint(_data,miner=miner, owner=account,network=network,
          offchaindata_platform=metadata_storage,dao=dao,access_code=request.args.get("access_code"))

  if len(rc["error"])==0:
    if not _ope is None:
      dao.add_histo(_ope["id"],"mint",account,nft.collection["name"],rc["result"]["transaction"],_ope["network"],"minage pour loterie")

    DAO(_data["domain"],_data["dbname"]).update(_data.toJson(),"quantity")

  return jsonify(rc)



@bp.route('/apply_filter/',methods=["POST"])
def apply_filter():
  body=request.json
  nft=ArtEngine()
  l=nft.get_layer(body["layer"])
  if l is None: return jsonify({"error":"layer unknonw"})

  rc=l.apply_filter(body["filter"])
  return jsonify({"error":"","images":rc})








@bp.route('/configs/<location>/',methods=["GET","DELETE"])
@bp.route('/configs/',methods=["GET","POST"])
#test http://127.0.0.1:4242/api/infos/
#test https://server.f80lab.com:4242/api/infos/
def configs(location:str="",format=""):
  """
  Chargement de la configuration de conception des NFT
  Utilisé par load_config
  :param location:
  :param format:
  :return:
  """

  user=request.args.get("user")
  if request.method=="GET" or format=="dict":

    if len(format)==0: format=request.args.get("format","json")
    if location.startswith("b64"): location=base64.b64decode(location[3:])

    if location.startswith("./"):
      rc=yaml.load(open(location,"r",encoding="utf8"),Loader=yaml.FullLoader)
      return [rc] if format=="dict" else jsonify([rc])

    if location.startswith("http"):
      r=requests.get(location)
      if r.status_code==200:
        rc=yaml.load(r.text,Loader=yaml.FullLoader)
        return [rc] if format=="dict" else jsonify([rc])
      else:
        raise RuntimeError("Impossible de trouver le fichier "+location)

    rc=DAO(config=current_app.config).get_docs(user=user,type_doc="config")
    for f in os.listdir(CONFIG_DIR):
      with open(CONFIG_DIR+f,"r",encoding="utf8") as file:
        config=yaml.load(file,Loader=yaml.FullLoader)
        if not "text" in config:config["text"]={}
        if not "text_to_add" in config["text"]:config["text"]["text_to_add"]=""

        if len(location)==0 or config["name"]==location:
          rc.append({"type_doc":"config","doc":config,"id":location})

    if format=="json": return jsonify(rc)
    if format=="file" and len(rc)>0:
      filename=rc[0]["location"]
      return send_file(path_or_file="./Configs/"+filename,mimetype="plain/text",as_attachment=True,download_name=filename)

    return rc

  if request.method=="DELETE":
    if user is None:
      os.remove("./Configs/"+location)
    else:
      DAO(config=current_app.config).del_doc(location,user=user,type_doc="config")
    return jsonify({"error":"","message":"fichier supprimé"})

  if request.method=="POST":
    doc = request.json
    platform=request.args.get("platform")
    if not platform is None:
      rc=upload_on_platform(doc,platform=platform)

      # filename="./Configs/"+doc["location"]
      #
      # #s["attributes"]=nft.attributes
      # s=str(yaml.dump(doc,default_flow_style=False,indent=4,encoding="utf8"),"utf8")
      #
      # log("Ecriture effective du fichier de contenu "+filename)
      # f=open(filename,"w",encoding="utf8")
      # f.write(s)
      # f.close()
      #
      # log("Fermeture du fichier")
      #

      return jsonify(rc)

  return returnError("Probleme technique")



# @bp.route('/accounts/<addr>/',methods=["GET"])
# @bp.route('/accounts/',methods=["GET"])
# def api_get_accounts(addr:str=""):
#   _network=get_network_instance(request.args.get("network","elrond-devnet"))
#   if len(addr)>0:
#     rc=_network.get_account(addr).__dict__
#   else:
#     rc=[]
#     for k in _network.get_keys():
#       obj=_network.get_account(k.address).__dict__
#       obj["name"]=k.name
#       rc.append(obj)
#
#   return jsonify(rc)


@bp.route('/users/<email>/',methods=["GET","POST"])
def api_users(email=""):
  dao=DAO(config=current_app.config)
  access_code=request.args.get("access_code")
  _network=get_network_instance(request.args.get("network","elrond-devnet"))
  u=dao.get_user(email,access_code,network_for_keys=_network.network)




@bp.route('/keys/',methods=["GET","POST"])
@bp.route('/accounts/',methods=["GET","POST"])
@bp.route('/accounts/<name>/',methods=["GET","POST"])
@bp.route('/keys/<name>/',methods=["DELETE","GET","POST"])
#https://metaboss.rs/set.html
#test http://127.0.0.1:4242/api/keys/
#test https://server.f80lab.com:4242/api/keys/
#http://127.0.0.1:4242/api/keys/?access_code=&network=elrond-devnet&with_private=true&with_balance=false&operation=
def keys(name:str=""):
  dao=DAO(config=current_app.config)
  _network=get_network_instance(request.args.get("network","elrond-devnet"))

  if request.method=="GET":
    with_balance=request.args.get("with_balance","false")=="true" or "accounts" in request.path
    operation=get_operation(request.args.get("operation"))

    if with_balance or "/accounts" in request.url:
      items=_network.get_accounts() if len(name)==0 else [_network.get_account(name)]
    else:
      items=_network.get_keys() if len(name)==0 else [_network.find_key(name)]
      if operation: items=items+extract_keys_from_operation(operation)

    return jsonify([item.__dict__ for item in items])


  if request.method=="DELETE":
    if _network.network_name=="polygon":
      filename=POLYGON_KEY_DIR+name+".secret"
    # else:
    #   filename=(SOLANA_KEY_DIR+name+".json").replace(".json.json",".json") if "solana" in _network.network_name else (ELROND_KEY_DIR+name+".pem").replace(".pem.pem",".pem")
    os.remove(filename)


  if request.method=="POST":
    obj=request.json
    if "secret_key" in obj:
      secret_key=obj["secret_key"]
    else:
      email=obj["email"]

      key:Key=create_account(email,dao=dao,
                                                    network=_network.network,
                                                    domain_appli=current_app.config["DOMAIN_APPLI"],
                                                    mail_new_wallet=obj["mail_new_wallet"] if "mail_new_wallet" in obj else None,
                                                    mail_existing_wallet=obj["mail_existing_wallet"] if "mail_existing_wallet" in obj else None)

    #dao.add_key_to_user(obj["email"],obj["access_code"],_network.network,secret_key,name)

  return jsonify({"message":"ok","address":key.address,"explorer":_network.getExplorer(key.address,"address"),"secret_key":key.secret_key})

#
#
# @bp.route('/refill/',methods=["GET"])
# #https://metaboss.rs/mint.html
# def refill():
#   addr=request.args.get("addr","")


# @bp.route('/scan/<token>',methods=["GET"])
# #http://127.0.0.1:4242/api/scan/HQwsV7o25ZPaDrBLHT7mDs2vbrAUjzujexF2aBkmLHZh
# def explorer(token:str):
#   network=request.args.get("network","solana-devnet")
#   format=request.args.get("format","json")
#   rc=Solana(network).scan(token)
#   if format=="json":
#     return jsonify(rc)
#   else:
#     return str(rc)




# @bp.route('/use/',methods=["GET"])
# #https://metaboss.rs/mint.html
# def use():
#   keyfile=request.args.get("keyfile","paul")
#   network=request.args.get("network","solana-devnet")
#   owner=request.args.get("owner")
#   account=request.args.get("account","")
#   rc=Solana(network).exec("use utilize",param="-h "+owner,account=account,keyfile=keyfile)
#   return jsonify(rc)




#https://server.f80lab.com:4242/api/images
#http://localhost:4242/api/images/
@bp.route('/images/<cid>',methods=["GET","DELETE"])
@bp.route('/images/',methods=["GET","DELETE"])
@bp.route('/files/<cid>',methods=["GET","DELETE"])
def get_image(cid:str=""):
  """
  note: l'upload des images se fait via l'api upload
  :param cid:
  :return:
  """
  if request.method=="GET":
    if len(cid)==0:
      #On retourne l'ensemble du répertoire
      return jsonify({"files":os.listdir(current_app.config["UPLOAD_FOLDER"])})
    else:
      file_to_download=request.args.get("f")

      if cid.startswith("obj_"):
        r=StoreFile().get(cid)
        return jsonify(r)

      if cid.startswith("db_"):
        r=DAO(cid=cid).get(cid)
        if not r is None:
          if "content" in r and "base64," in r["content"]:
            data=r["content"]
            format=data.split("base64,")[0].replace("data:","")
            f=BytesIO(base64.b64decode(data.split("base64,")[1]))
          else:
            return jsonify(r)
        else:
          return returnError("Image introuvable")
      else:
        #Analyse du cid
        ext=cid.split(".")[1] if "." in cid else "webp"
        format="application/"+ext
        if ext in ["webp","jpg","jpeg","gif","png"]:format="image/"+ext
        if ext=="svg": format="image/svg+xml"
        if ext in ["json","yaml","txt"]: format="text/"+ext

        #if "store_f" in cid and len(cid.split("_"))>1: file_to_download=str(base64.b64decode(cid.split("__f")[1].split("_")[0]),"utf8")
        filename=current_app.config["UPLOAD_FOLDER"]+cid
        if not exists(filename): return returnError("Fichier inexistant",status=404)

        if format.startswith("text/"):
          f=open(filename,"r")
        else:
          f=open(filename,"rb")


      response = make_response(f.read())
      response.headers.set('Content-Type', format)
      if file_to_download and not format.startswith("image") and not format.startswith("video"):
        file_to_download=str(base64.b64decode(file_to_download),"utf8")
        response.headers.set('Content-Disposition','attachment;filename='+file_to_download)

      return response



  if request.method=="DELETE":
    if "/api/images/" in cid:cid=cid.split("/api/images/")[1].split("?")[0]
    if exists(current_app.config["UPLOAD_FOLDER"]+cid):rc=os.remove(current_app.config["UPLOAD_FOLDER"]+cid)
    return "Ok",200


@bp.route('/json/<cid>',methods=["GET"])
def get_json(cid:str):
  dao=DAO(config=current_app.config)
  rc=dao.get_dict(cid)
  if rc is None:rc={}
  if "_id" in rc: del rc["_id"]
  return jsonify(rc)



# @bp.route('/sign/',methods=["GET"])
# #https://metaboss.rs/mint.html
# def sign():
#   creator=request.args.get("creator","")
#   keyfile=request.args.get("keyfile","paul")
#   network=request.args.get("network","solana-devnet")
#   account=request.args.get("account","")
#   log("Demande de signature pour "+keyfile)
#   rc={}
#   if len(account)>0:
#     rc=Solana(network).exec("sign one",account=account,keyfile=keyfile)
#   return jsonify(rc)




#
# @bp.route('/nft/<owner>/<tokenid>/',methods=["GET"])
# def get_nft(owner:str,tokenid:str):
#   network=request.args.get("network","solana-devnet")
#   if "elrond" in network:
#     nft=Elrond(network).get_nft(owner=owner,token_id=tokenid)
#   return jsonify(nft)
#


#https://server.f80lab.com:4242/api/nfts/
#usage avec get_transaction
#http://127.0.0.1:4242/api/nfts/?network=polygon-devnet&account=admin
@bp.route('/nfts/',methods=["GET"])
@bp.route('/nfts/<id>/',methods=["GET"])
def nfts(id=""):
  """
  Récupération des NFTS appartement à un compte ou d'un nft en particulier
  :param id: id/address du nft
  :return:
  """
  network=request.args.get("network","elrond-devnet")
  account=request.args.get("account","paul")
  with_attr=("with_attr" in request.args) and (not "with_attr=false" in request.args)
  limit=int(request.args.get("limit","100"))
  offset=int(request.args.get("offset","0"))

  log("Récupération de "+str(limit)+" nfts sur "+network+" à partir de "+str(offset))

  rc=[]
  _network=get_network_instance(network)
  if id=="":
    l_nfts=_network.get_nfts(account,limit,with_attr=with_attr,offset=offset,with_collection=True)
  else:
    l_nfts=[_network.create_nft(token_id=id, attr=True)]

  log(str(len(l_nfts))+" NFT identifiés")

  return jsonify([x.__dict__ for x in l_nfts])




@bp.route('/access_code_checking/<access_code>/<addr>/',methods=["GET"])
@bp.route('/access_code_checking/<access_code>/',methods=["GET"])
#http://127.0.0.1:4242/api/access_code_checking/42714280/
#http://server.f80lab.com:4242/api/access_code_checking/42714280/
def access_code_checking(access_code:str,addr:str=""):
  if access_code==SECRET_ACCESS_CODE or get_access_code_from_email(addr)==access_code:
    return jsonify({"message":"ok"})
  else:
    return returnError("Incorrect access code")


@bp.route('/check_private_key/<seed>/<addr>/<network>/',methods=["GET"])
#http://127.0.0.1:4242/api/access_code_checking/
def check_private_key(seed:str,addr:str,network:str):
  if addr.startswith("erd"):
    _account=Elrond(network=network).toAccount(seed)
    if _account.address.bech32()==addr:
      return jsonify({"message":"ok"})


  return returnError("Incorrect access code")




# @bp.route('/validate/',methods=["GET"])
# #http://127.0.0.1:4242/api/validate/?q=symbol1&ope=calvi2022&network=devnet
# def validate():
#   rc=dict()
#
#   query=request.args.get("q","")
#   operation=request.args.get("ope","").lower()
#   network=request.args.get("network","solana-devnet").lower()
#
#   _ope=open_operation(operation)
#   if _ope:
#     with open(OPERATIONS_DIR+_ope["data"]) as csvFile:
#       data=csv.DictReader(csvFile,delimiter=";")
#       for l in list(data):
#         if l[_ope["find"]["field"]]==query:
#           nft=Solana(network).get_token(l["address"],network)
#           if nft[_ope["to_check"]] in _ope["values"]:rc={"validity":"ok"}
#
#   return jsonify(rc)


# @bp.route('/token_by_delegate/',methods=["GET"])
# #http://127.0.0.1:4242/api/token_by_delegate/?account=LqCeF9WJWjcoTJqWp1gH9t6eYVg8vnzUCGBpNUzFbNr
# def get_token_by_delegate():
#   network=request.args.get("network","solana-devnet")
#   account=request.args.get("account","")
#   rc=Solana(network).get_token_by_miner(account)
#   return jsonify(rc)


@bp.route('/rescue_wallet/<email>/',methods=["GET"])
#http://127.0.0.1:4242/api/token_by_delegate/?account=LqCeF9WJWjcoTJqWp1gH9t6eYVg8vnzUCGBpNUzFbNr
def api_rescue_wallet(email:str):
  network=request.args.get("network","elrond-mainnet")
  db=request.args.get("db","db-server-nfluent")
  addr=DAO(network=db).get_address(email,network)
  if addr is None:
    return jsonify({"message":"Le mail "+email+" est inconnu"})
  else:
    _net=get_network_instance(network)
    domain_appli=current_app.config["DOMAIN_APPLI"]
    send_mail(open_html_file("mail_rescue_wallet",{
      "wallet_address":addr,
      "mini_wallet":_net.nfluent_wallet_url(addr,domain_appli),
    },domain_appli=domain_appli),email,subject="Récupération de votre wallet")

    return jsonify({"message":"Mail envoyé"})

  

@bp.route('/encrypt_key/<network>/',methods=["POST"])
#http://127.0.0.1:4242/api/token_by_delegate/?account=LqCeF9WJWjcoTJqWp1gH9t6eYVg8vnzUCGBpNUzFbNr
def encrypt_key(network:str):
  '''
  Encrypt une clé privée pour intégration dans un fichier d'opération
  :param network:
  :return:
  '''
  secret_key=request.json["secret_key"]
  name=request.json["alias"]
  address=request.json["address"] if "address" in request.json else ""

  if secret_key=="" and len(name)>0:
    key=get_network_instance(network).find_key(name if len(name)>0 else address)
  else:
    if len(address)==0: address=get_network_instance(network).toAddress(secret_key)
    key=Key(name=name,secret_key=secret_key,network=network,address=address)

  return jsonify({"encrypt":key.encrypt(),"address":key.address,"private_key":key.encrypt(True)})



@bp.route('/send_email_to_validateur/',methods=["POST"])
@bp.route('/send_email_to_validateur/<user>',methods=["POST"])
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
      },domain_appli=current_app.config["DOMAIN_APPLI"]),validateur,subject=operation["title"]+" connexion à l'application de validation")

  return jsonify({"error":""})




@bp.route('/send_transaction_confirmation/<email>/',methods=["POST"])
def send_transaction_confirmation(email:str):
  body=request.json
  send_mail(open_html_file("transaction_confirmation",{
    "n_passes":body["n_passes"],
    "nft_url":body["nft_url"],
    "nft_title":body["nft_title"]
  },domain_appli=current_app.config["DOMAIN_APPLI"]),email,subject="Utilisation de votre NFT pour obtenir votre passe")
  return jsonify({"error":""})





@bp.route('/extract_zip/',methods=["POST"])
def extract_zip():
  pass


@bp.route('/upload/',methods=["POST"])
def upload():
  """
  Chargement des visuels
  :return:
  """
  platform=request.args.get("platform","ipfs")
  _type=request.args.get("type")

  if str(request.data,"utf8").startswith("{"):
    body=request.json
  else:
    content=str(request.data,"utf8")
    if _type is None:
      for ext in ["GIF","WEBP","PNG","JPEG"]:
        if ext in content[:30]:_type="image/"+ext.lower()

    if not "base64" in content and not "<svg" in content and not _type is None:
      content=_type+";base64,"+str(base64.b64encode(request.data),"utf8")

    if not _type is None:
      body={
        "filename":get_filename_from_content(content,"store",_type),
        "content":content,
        "type":_type
      }
      if "svg" in _type:
        if "base64" in body["content"] and body["content"].index("base64")<200:     #On suppose que le fichier SVG est intégralement code en base64
          body["content"]=str(base64.b64decode(body["content"].split("base64,")[1]),"utf8")
        else:
          format=request.args.get("convert","")
          if format!="":
            log("Conversion du fichier au format "+format)
            buffered=convert_to(body["content"],format=format,quality=95)
            body["content"]="data:image/"+format+";base64,"+str(base64.b64encode(buffered.getvalue()),"utf8")
            body["type"]="image/"+format
    else:
      body=content


  if _type=="qrcode":
    log("Enregistrement d'un qrcode")
    buffered = BytesIO()
    pyqrcode.create(body["filename"].split("qrcode:")[1]).png(buffered,scale=3)

    body["content"]=";base64,"+str(base64.b64encode(buffered.getvalue()),"utf8")
    body["filename"]=get_filename_from_content(body["content"],"store","png")
    body["type"]="image/png"




  #TODO: probablement a revoir
  # if body["type"].startswith("image/zip"):
  #   rc=[]
  #   b=BytesIO(base64.b64decode(body["content"].split("base64,")[1]))
  #   with py7zr.SevenZipFile(b, 'r') as zip:
  #     zip.extractall(".")
  #     for fname in zip.getnames():
  #       rc.append(upload_on_platform({
  #         "filename":fname,
  #         "type":"image/"+fname[fname.rindex('.')+1:]
  #       },platform))

  rc=upload_on_platform(body,platform,
                        domain_server=current_app.config["DOMAIN_SERVER"],
                        upload_dir=current_app.config["UPLOAD_FOLDER"])

  return jsonify(rc)



@bp.route('/upload_metadata/',methods=["POST"])
def upload_metadata():
  network=request.args.get("network","solana-devnet")

  _data=request.json
  id=request.args.get("filename_for_metadata",None)
  repo=request.args.get("repository","CalviOnTheRocks2022")
  offchaindata_platform=request.args.get("offchaindata_platform","ipfs").replace(" ","").lower()
  _network=get_network_instance(network)

  rc=upload_on_platform(_network.prepare_offchain_data(_data),offchaindata_platform,id=id,
                        options={"repository":repo},
                        upload_dir=current_app.config["UPLOAD_FOLDER"])

  return jsonify(rc)







@bp.route('/create_collection/',methods=["POST"])
def api_create_collection():
  """
  API de création d'une collection
  :param owner:
  :return:
  """
  _data=request.json
  network=request.args.get("network","elrond-devnet")
  if network.startswith("db-"):
    return returnError("Impossible d'utiliser une base de données comme réseau cible d'une collection")

  _net=get_network_instance(network) #DAO(config=current_app.config).get_user_from_access_code(request.args.get("access_code"))

  miner=Key(obj=_data["owner"])

  solde=_net.balance(miner.address)
  collection=_net.add_collection(miner,collection_name=_data["name"],type_collection=_data["type"],options=_data["options"])
  if collection is None:
    return returnError("Cette collection existe déjà")

  new_collection=_net.get_collection(collection["id"])
  new_solde=_net.balance(miner.address)

  return jsonify({
    "collection":new_collection,
    "cost":solde-new_solde
  })




# def mint(nft:NFT,miner,owner,network,offchaindata_platform="IPFS",storagefile="",mail_new_wallet="",mail_existing_wallet="",operation_id="",encrypt_nft=False):
#   """
#   minage du NFT
#   :param nft:
#   :param miner:
#   :param owner:
#   :param network:
#   :param offchaindata_platform:
#   :param storagefile:
#   :param wallet_appli:
#   :return:
#   """
#   if len(mail_existing_wallet)==0:mail_existing_wallet="mail_existing_account"
#   if len(mail_new_wallet)==0:mail_new_wallet="mail_new_account"
#
#   rc= {"error":"Problème technique"}
#   account=None
#
#   collection_id=nft.collection["id"] if not nft.collection is None and "id" in nft.collection else ""
#   if collection_id=="":
#     returnError("!La collection est indispensable")
#
#   if nft.address.startswith("db_") and nft.marketplace["quantity"]==0:
#     returnError("!Ce NFT n'est plus disponible")
#
#   dao_histo=DAO(ope=get_operation(operation_id))
#
#   if miner and len(miner)>0:
#     if (not owner or owner=="undefined" or owner=="") and not "db-" in network:owner=miner
#   else:
#     miner=owner
#   nft.miner=miner
#
#   if is_email(owner):
#     email=owner
#     if "elrond" in network:
#       elrond=Elrond(network)
#       _account,pem,words,qrcode=elrond.create_account(email=email,histo=dao_histo,
#                                                       subject="Votre NFT '"+nft.name+"' est disponible",
#                                                       domain_appli=current_app.config["DOMAIN_APPLI"],
#                                                       mail_new_wallet=mail_new_wallet,mail_existing_wallet=mail_existing_wallet)
#       account=_account.address.bech32()
#       log("Notification de "+owner+" que son compte "+elrond.getExplorer(account,"account")+" est disponible")
#
#     if "solana" in network:
#       solana=Solana(network)
#       words,pubkey,privkey,list_int=solana.create_account(domain_appli=current_app.config["DOMAIN_APPLI"],subject="Votre NFT '"+nft.name+"' est disponible")
#       account=pubkey
#
#     if "polygon" in network:
#       words,pubkey,privkey,list_int=Polygon(network).create_account(domain_appli=current_app.config["DOMAIN_APPLI"],histo=dao_histo,
#                                                                     subject="Votre NFT '"+nft.name+"' est disponible")
#       account=pubkey
#
#
#   if account is None:
#     if "elrond" in network:
#       elrond=Elrond(network)
#       account=elrond.toAccount(owner)
#       if account is None:
#         log("Impossible de reconnaitre "+owner)
#       else:
#         account=account.address.bech32()
#
#     # if not _ope is None:
#     #   dao.add_histo(_ope["id"],"new_account",account,"","",_ope["network"],"Création d'un compte pour "+owner,owner)
#
#
#   if "polygon" in network:
#     rc=Polygon(network).mint(
#       miner,
#       title=nft.name,
#       description=nft.description,
#       tags=nft.tags,
#       collection=None,
#       properties=nft.attributes,
#       files=nft.files,
#       ipfs=IPFS(IPFS_SERVER),
#       quantity=nft.marketplace["quantity"],
#       royalties=nft.royalties,  #On ne prend les royalties que pour le premier créator
#       visual=nft.visual,
#       creators=nft.creators
#     )
#
#
#   if "elrond" in network.lower() and not account is None:
#     elrond=Elrond(network)
#     old_amount=elrond.get_account(miner)["amount"]
#     if old_amount==0:
#       return returnError("Solde du mineur insuffisant")
#
#     if nft.address.startswith("file_") or nft.address.startswith("db_") or len(nft.address)==0:
#       nonce,rc=elrond.mint(miner,
#                               title=nft.name,
#                               description=nft.description,
#                               tags=nft.tags,
#                               collection=collection_id,
#                               properties=nft.attributes,
#                               files=nft.files,
#                               ipfs=IPFS(IPFS_SERVER),
#                               quantity=nft.marketplace["quantity"] if not nft.marketplace is None and "quantity" in nft.marketplace else 1,
#                               royalties=nft.royalties,  #On ne prend les royalties que pour le premier créator
#                               visual=nft.visual,
#                               creators=nft.creators
#                               )
#     else:
#       rc={"error":"NFT deja miné","hash":"","result":{"mint":nft.address}}
#       collection_id,nonce = elrond.extract_from_tokenid(nft.address)
#
#     if nonce is None:
#       rc["error"]="Problème technique" if not "error" in rc else rc["error"]
#       rc={"error":"Mint error: "+rc["error"],"hash":rc["hash"]}
#     else:
#
#       infos=elrond.get_account(miner)
#       token_id=collection_id+"-"+nonce
#
#       if elrond.toAccount(miner).address.bech32()!=account:
#         rc=elrond.transfer(collection_id,nonce,miner,account)
#         if not rc or len(rc["error"])>0:
#           return rc
#         send(current_app,"nfwallet_"+miner,{"action":"refresh"})
#
#       solde=elrond.get_account(miner)["amount"]-old_amount
#       rc={"command":"ESDTCreate",
#           "error":"",
#           "link":elrond.getExplorer(token_id,"nfts"),
#           "uri":"",
#           "out":"",
#           "hash":rc["hash"],
#           "cost":solde,
#           "result":{
#             "transaction":token_id,
#             "mint":token_id
#           },
#           "unity":"EGLD",
#           "link_transaction":elrond.getExplorer(token_id,"nfts"),
#           "link_mint":elrond.getExplorer(token_id,"nfts"),
#           "balance":int(infos["balance"])/1e18
#           }
#
#   if "solana" in network.lower():
#     solana=Solana(network)
#     offchain_uri=upload_on_platform(solana.prepare_offchain_data(nft.attributes),offchaindata_platform,
#                                     id=request.args.get("filename_for_metadata",None),
#                                     options={"repository":request.args.get("repository","calviontherock")},
#                                     )["url"]
#     #voir https://metaboss.rs/mint.html
#     #(request.args.get("sign","True")=="True" or request.args.get("sign","all")=="all")
#     rc=solana.mint(nft,miner=miner,sign=False,owner=request.args.get("owner",""))
#
#     if request.args.get("sign_all","False")=="True" and "result" in rc and "mint" in rc["result"]:
#       signers=[x["address"] for x in nft.creators]
#       #signers.remove(solana.find_address_from_json(keyfile))
#       solana.sign(rc["result"]["mint"],signers)
#
#   # Transfert des NFTs vers la base de données
#   if "database" in network.lower() or "db-" in network.lower():
#     _dao=DAO(network=network)
#     if _dao.isConnected():
#       rc=_dao.mint(nft,ope=operation_id)
#     else:
#       log("Impossible de se connecter")
#
#
#   if network.startswith("file"):
#     storefile=StoreFile(network=network,domain_server=current_app.config["DOMAIN_SERVER"])
#     rc=storefile.mint(nft)
#     if encrypt_nft:
#       rc["out"]=encrypt(rc["out"],format="txt")
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
#   if ("result" in rc) and ("transaction" in rc["result"]) and (network!="file"):
#     if nft.address.startswith("db_") and not network.startswith("db-"): #Pas de mise a jour si la blockchain cible était la base de donnée
#       DAO(nft.address.split("/")[1]).update_quantity(nft.address,-1)
#     try:
#       ope=request.args.get("ope","")
#     except:
#       ope=""
#     dao_histo.add_histo(ope,"mint",miner,collection_id,rc["result"]["transaction"],network,"Minage")
#
#   return rc


@bp.route('/set_role_for_collection/',methods=["POST"])
def set_role_for_collection():
  collection_id=request.json['collection_id']
  owner=request.json['owner']
  network=request.json["network"]
  if "elrond" in network:
    t=Elrond(network).add_account_to_collection({"id":collection_id}, owner)
    return jsonify({"transaction":t})





@bp.route('/mint/',methods=["POST"])
def api_mint():
  """
  Minage des NFT sur les différents réseaux possibles : elrond, solana, base de donnée, fichier json
  :return:
  """
  offchaindata_platform=request.args.get("offchaindata_platform","nftstorage")
  _nft=NFT(object=request.json["nft"])
  _miner=Key(obj=request.json["miner"])
  owner=request.args.get("owner",_miner.address)
  # _ope=get_operation(request.args.get("operation",""))
  config=current_app.config
  dao=DAO(config=config)

  network:Network=get_network_instance(request.args.get("network","elrond-devnet"))
  #network.add_keys(_ope,dao.get_user_from_access_code(request.args.get("access_code")))

  if is_email(owner):
    return returnError("Il est nécessaire de créer un compte préalablement pour "+owner)
    # mail_new_wallet="" if _ope is None else _ope["new_account"]["mail"]
    # mail_existing_wallet="" if _ope is None else _ope["transfer"]["mail"]
    # create_account(owner,network,config["DOMAIN_APPLI"],config["DB_MAIN"],mail_new_wallet,mail_existing_wallet,_nft.name)

  try:
    rc=mint(_nft,_miner,owner,
            network=network,
            offchaindata_platform=offchaindata_platform,
            domain_server=current_app.config["DOMAIN_SERVER"],
            dao=dao,
            encrypt_nft=(request.args.get("encrypt_nft")=="true"))
  except Exception as inst:
    return returnError(inst)

  if not _nft.visual.startswith("http"):
    return jsonify({"error":"Vous devez uploader les images avant le minage"})

  return jsonify(rc)




@bp.route('/mint_from_file/',methods=["POST"])
#https://metaboss.rs/mint.html
def mint_from_file():
  ipfs=IPFS(IPFS_SERVER,5001)

  keyfile=request.args.get("account","paul")
  sign=request.args.get("sign",False)

  files:FileStorage = request.files.getlist('files')
  _datas=dict()
  for file in files:
    if "image" in file.content_type:
      cid=ipfs.add_file(file)
      _datas[file.filename]=ipfs.get_link(cid["Hash"])
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

      file_to_mint=current_app.config["UPLOAD_FOLDER"]+"to_mint"+datetime.datetime.now().timestamp()+".json"
      with open(file_to_mint, 'w') as f:
        f.writelines(json.dumps(_data))
        f.close()

      rc=exec("mint one","--nft-data-file "+file_to_mint+(" --sign" if sign else ""),keyfile=keyfile)
      if len(rc["error"])==0:os.remove(file_to_mint)

  return jsonify({"error":rc["error"],"message":rc["result"]})



# import pandas as pd
#
# @bp.route('/mint_from_file/<ope>/',methods=["POST"])
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



@bp.route('/update_obj/',methods=["POST"])
def update_obj():
  ipfs=IPFS(IPFS_SERVER,5001)
  network=request.args.get("network")
  keyfile=request.args.get("keyfile")
  account=request.args.get("account")


  _network=get_network_instance(network)
  rc=_network.update(
    user=keyfile,
    token_id=account,
    properties=request.json,
    ipfs=ipfs
  )
  return rc

  # else:
  #   cid=ipfs.add(request.json)
  #   url=ipfs.get_link(cid["Hash"])
  #   return Solana(network).exec("update","uri --new-uri "+url,account=account,keyfile=keyfile)


@bp.route('/export/',methods=["POST"])
def export():
  ipfs=IPFS(IPFS_SERVER,5001)
  i=0
  with ZipFile('./Temp/archive.7z', 'w') as myzip:
    for token in request.json:
      file_to_mint=current_app.config["UPLOAD_FOLDER"]+str(i)+".json"
      with open(file_to_mint, 'w') as f:
        f.writelines(json.dumps(token,indent=4, sort_keys=True))
        f.close()

      myzip.write(file_to_mint)
      i=i+1

    myzip.close()
  cid=ipfs.add_file('./Temp/archive.7z')
  return jsonify({"zip_file":ipfs.get_link(cid)})





@bp.route('/validators/',methods=["GET","POST"])
@bp.route('/validators/<validator>/',methods=["PUT","GET","DELETE"])
def validators(validator=""):
  """

  :param validator:
  :return:
  """
  dao=DAO(config=current_app.config)
  if request.method=="GET":
    rc=[]
    log("On demande la liste des validateurs")
    for val in list(dao.db["validators"].find()):
      if len(validator)==0 or validator==val["id"]: #Validator opére comme un filtre
        del val["_id"]
        val["access_code"]=encrypt(val["id"])
        rc.append(val)
    return jsonify(rc)

  if request.method=="DELETE":
    send(current_app,"refresh")
    dao.db["validators"].delete_one({"id":validator})
    return jsonify({"message":"deleted"})

  if request.method=="POST":
    validator_name="val_"+now("hex") if len(request.json["validator_name"])==0 else request.json["validator_name"]
    log("Un validateur demande son inscription. Attribution du nom="+validator_name)
    access_code=encrypt(validator_name)
    ask_for:str=request.json["ask_for"]
    if not dao.add_validator(validator_name,ask_for):
      return returnError("Impossible d'inscrire le validateur")
    else:
      send(current_app,"refresh")

    nfts=[]
    if ask_for.startswith("operation:"):
      operation=open_operation(ask_for.split("operation:")[1])
      elrond=Elrond(operation["network"])
      log("On retourne la liste des propriétaire des NFT des sources de l'operation "+ask_for)
      for nft in get_nfts_from_src(operation["data"]["sources"]):
        if len(operation["validate"]["filters"]["collections"])==0 or nft.collection in operation["validate"]["filters"]["collections"]:
          if not nft.owner: nft=elrond.get_nft(nft.address)
          nfts.append(nft)
      owners=[x.owner for x in nfts]
    else:
      log("On retourne la liste des propriétaire des NFTs de la collection: "+ask_for)
      elrond=Elrond(request.json["network"])
      owners=list(set([x.owner for x in elrond.get_nfts_from_collections(ask_for.split(","))]))

    return jsonify({
      "access_code":access_code,
      "id":validator_name,
      "addresses":owners
    })


  if request.method=="PUT":
    rc=dao.db["validators"].update_one({"id":validator},{"$set":request.json})
    return jsonify({"message":"ok"})



@bp.route('/registration/<email>/',methods=["GET"])
def api_registration(email:str):
  rc=DAO(config=current_app.config).registration(email,current_app.config["DEFAULT_PERMISSIONS"])
  if "already" in rc["message"]:
    send_mail(open_html_file("resend_mail_registration",{
      "tokenforge_url":current_app.config["DOMAIN_APPLI"],
      "access_code":rc["access_code"]
    }),_to=email,subject="Renvoi du code d'accès")
  else:
    send_mail(open_html_file("mail_registration",{
      "tokenforge_url":current_app.config["DOMAIN_APPLI"],
      "access_code":rc["access_code"]
    }),_to=email,subject="Inscription à tokenforge")
  return jsonify(rc)


@bp.route("/login/<email>/<access_code>/", methods=["GET"])
def api_login(email:str,access_code:str):
  """
  Create a route to authenticate your users and return JWTs. The
  create_access_token() function is used to actually generate the JWT.
  voir https://flask-jwt-extended.readthedocs.io/en/stable/basic_usage/
  :return:
  """
  if access_code==SECRET_ACCESS_CODE:
    user={"email":ADMIN_EMAIL,"perms":ADMIN_PERMS,"routes":[],"access_code":access_code}
  else:
    user=DAO(config=current_app.config).get_user(email=email,access_code=access_code)
    if user is None:
      return returnError("Code d'accès inconnu")

  if request.args.get("with_api","False").lower()=="true":
    user["access_token"] = create_access_token(identity=user["email"])

  return jsonify(user)



@bp.route('/delete_user/<email>/<access_code>/',methods=["DELETE"])
def api_delete_account(email:str,access_code:str):
  if DAO(config=current_app.config).delete_user(email,access_code):
    return jsonify(message="User deleted")
  else:
    return returnError("Le compte n'a pas été supprimé")


@bp.route('/send_to_validator/<validator_id>/',methods=["POST"])
def api_send_to_validator(validator_id:str):
  """
  Permet l'envoi d'un message du serveur au validateur
  :param validator_id:
  :return:
  """
  message=request.json["message"]
  rc=send(current_app,validator_id, {"message":message})
  return jsonify({"message":"sended"})




@bp.route('/search_images/',methods=["GET"])
def api_search_image():
  """
  Permet la recherche d'image
  :return:
  """
  query=request.args.get("query")

  rc=queryPixabay(query,limit=20 if "sticker" in query else 10)+queryUnsplash(query,limit=0 if "sticker" in query else 10)
  return jsonify({"images":rc})




@bp.route('/remove_background/',methods=["POST"])
def api_remove_background():
  """
  Effectue un retrait de l'image de fond
  Ne fonctionne que sur le serveur (nom compatible avec windows)
  :return:
  """
  work_dir=current_app.config["UPLOAD_FOLDER"]
  input:Image=Sticker(image=request.json["image"],work_dir=work_dir).image
  domain_server=current_app.config["DOMAIN_SERVER"]
  if not isLocal(domain_server):
    log("Lancement de la suppression du fond")
    import rembg
    output=rembg.remove(input)
    return jsonify({"image":Sticker(image=output,work_dir=work_dir).toBase64()})
  else:
    return jsonify({"image":Sticker(image=input,work_dir=work_dir).toBase64(),"error":"Impossible de supprimer le fond depuis windows"})






@bp.route('/scan_for_access/',methods=["POST"])
def scan_for_access():
  """
  Validation de la connexion via le nfluent wallet en mode wallet_connect.
  Cette api est appelé par le visiteur via la webcam du nfluent wallet
  il transmet dans le body le code du validateur et l'adresse de son wallet
  :return:
  """
  _data=request.json
  if not _data["validator"] or len(_data["validator"])==0: log("Le client doit spécifier le validateur en charge de la validation")
  if "/api/qrcode/" in _data["validator"]:_data["validator"]=_data["validator"].split("/api/qrcode/")[1]

  validator=decrypt(_data["validator"])
  log("Le validateur en charge de la validation : "+validator)

  log("Le serveur transmet au validateur "+validator+" l'adresse du wallet ayant réalisé le flashage "+_data["address"])
  rc=send(current_app,validator, {"address":_data["address"]})

  log("Ajout de l'adresse "+_data["address"]+" pour validation dans la base")
  DAO(config=current_app.config).db["validators"].update_one({"id":validator},{"$set": {"user":_data["address"]}})
  return jsonify({"message":"ok"})





#voir https://metaboss.rs/burn.html
#http://127.0.0.1:9999/api/burn/?account=GwCtQjSZj3CSNRbHVVJ7MqJHcMBGJJ9eHSyxL9X1yAXy&url=
#TODO: ajouter les restrictions d'appel
@bp.route('/burn/')
def burn():
  account=request.args.get("account")
  keyfile=request.args.get("keyfile")
  delay=request.args.get("delay","1.0")
  network=request.args.get("network","solana-devnet")

  if "elrond" in network:
    rc=Elrond(network).burn(keyfile,account)
  # else:
  #   rc=Solana(network).exec("burn one",account=account,keyfile=keyfile,delay=int(delay))

  return jsonify(rc)

