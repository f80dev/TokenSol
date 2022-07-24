


import base64
import csv
import datetime
import hashlib
import json
import os
import ssl
import sys

from copy import copy

from io import BytesIO, StringIO
from os.path import exists
from random import random

from zipfile import ZipFile

import py7zr
import pyqrcode
import requests
import yaml
from PIL.Image import Image

from flask import request, jsonify, send_file, Flask, make_response
from flask_cors import CORS
from fontTools import ttLib
from reportlab.graphics import renderPM
from solana.account import Account
from svglib.svglib import svg2rlg

from werkzeug.datastructures import FileStorage
from yaml import dump, Dumper

import GitHubStorage
from ArtEngine import ArtEngine, Layer, Sticker, convert_to_gif
from Elrond.Elrond import Elrond, ELROND_KEY_DIR
from GoogleCloudStorageTools import GoogleCloudStorageTools
from NFT import NFT
from PrestaTools import PrestaTools
from dao import DAO

from ftx import FTX
from Solana.Solana import SOLANA_KEY_DIR, Solana
from Tools import hex_to_str, log, filetype, now, is_email, send_mail, open_html_file, encrypt, decrypt, setParams, \
  str_to_hex
from infura import Infura
from ipfs import IPFS
from nftstorage import NFTStorage
from secret import GITHUB_TOKEN, SALT, ENCRYPTION_KEY, GITHUB_ACCOUNT, PERMS

app = Flask(__name__)
ftx=FTX()
nft=ArtEngine()
dao=DAO()


#voir la documentation de metaboss:

IPFS_PORT=5001
IPFS_SERVER="/ip4/75.119.159.46/tcp/"+str(IPFS_PORT)+"/http"



def returnError(msg:str="",_d=dict()):
  log("Error "+msg)
  _d["error"]="Ooops ! Petit problème technique. "+msg
  return jsonify(_d),500



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
def getyaml(name,format="json"):
  dir=request.args.get("dir",".")
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
#test http://127.0.0.1:4242/api/test/
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



@app.route('/api/test2/')
#test http://127.0.0.1:4242/api/test2
def test():
  nfts=ftx.get_nfts_balances()
  return "Ok",201




@app.route('/api/reset_collection/',methods=["GET"])
#test http://127.0.0.1:4242/api/test/
def reset_collection():
  nft.reset()
  return jsonify({"status":200})


@app.route('/api/fonts/',methods=["GET"])
#test http://127.0.0.1:4242/api/fonts/
def get_fonts():
  rc=[]
  for f in os.listdir("./Fonts"):
    tt = ttLib.TTFont("./Fonts/"+f)
    info=tt.get("name")
    if info:
      try:
        rc.append({"name":str(info.names[1].string,"utf8")+" "+str(info.names[2].string,"utf8"),"file":f})
      except:
        pass
  return jsonify({"fonts":rc})



@app.route('/api/layers/',methods=["POST"])
#test http://127.0.0.1:4242/api/test/
def layers(body=None):
  if body is None: body=request.json
  if not "name" in body:
    return "Syntaxe error for this layer",500
  name=body["name"]
  limit=int(request.args.get("limit","0"))
  log("Generation de la couche "+name)
  nft.delete(name) # <-- cette instance ne devrait plus être partagés dans une optique multi-usage
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
    if elt:
      if "text" in elt and elt["text"]:
        s=Sticker(text=elt["text"]["text"],x=elt["text"]["x"],y=elt["text"]["y"],
                  dimension=(elt["text"]["dimension"][0],elt["text"]["dimension"][1]),
                  fontstyle=elt["text"]["fontstyle"])
      else:
        if elt["image"] and len(elt["image"])>0:
          s=Sticker(image=elt["image"])

      if s: layer.add(s)


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
  if "base64" in str(request.data,"utf8"):
    _data=yaml.load(str(base64.b64decode(str(request.data,"utf8").split("base64,")[1]),"utf8"))
  else:
    _data=request.json

  _data=_data["svg"]

  index=0
  max_index=len(_data["files"])
  for l in _data["layers"]:
    if not "unique" in l or not l["unique"]:
      max_index=max_index*len(l["values"])

  rc=[]
  histo=[]
  while True:
    filename="./temp/"+_data["files"][int(random()*len(_data["files"]))]
    h=filename
    with open(filename,"r") as f:
      svg=" ".join(f.readlines())
    f.close()

    for l in _data["layers"]:
      value=l["values"][int(random()*len(l["values"]))]
      h=h+str(value)
      svg=svg.replace(l["key"],value)

    if not h in histo:
      histo.append(h)
      index=index+1
      if index==max_index: break
      if request.args.get("format","json")=="file":
        pass
        #renderPM.drawToFile(svg2rlg(svg),"./temp/image"+str(index)+".png",fmt="PNG")
      else:
        filename="./temp/temp.svg"
        f=open(filename,"w")
        f.write(svg)
        f.close()
        image=renderPM.drawToPIL(svg2rlg(filename)).convert("RGBA")
        newImage = []
        for item in image.getdata():
          if item[:3] == (255, 255, 255):
            newImage.append((255, 255, 255, 0))
          else:
            newImage.append(item)

        image.putdata(newImage)

        s=Sticker(image=image.convert("RGBA"))
        rc.append(s.toBase64())
        #rc.append("data:image/gif;base64,"+str(base64.b64encode(),"utf8"))

  return jsonify(rc)



@app.route('/api/collection/')
#test http://127.0.0.1:4242/api/test/
def get_collection(limit=100,format=None,seed=0,size=(500,500),quality=100):
  """
  Generation de la collection des NFTs
  :param limit:
  :param format:
  :param seed:
  :param ext:
  :param size:
  :return:
  """
  if format!="list": #Dans le cas de format = list cette fonction est appelé depuis le serveur (pas depuis une api)
    limit=int(request.args.get("limit",10))
    size=request.args.get("size","500,500").split(",")
    format=request.args.get("format","zip")
    quality=request.args.get("quality",98)
    seed=int(request.args.get("seed","0"))
    ext=request.args.get("image","webp")
    data=request.args.get("data","")
    nft.name=request.args.get("name","mycollection").replace(".png","")

  log("On détermine le nombre d'image maximum générable")
  max_item=1
  for layer in nft.layers:
    if layer.indexed:
      max_item=max_item*len(layer.elements)

  files=nft.generate(
    dir="./temp/",
    limit=min(limit,max_item),
    seed_generator=seed,
    width=int(size[0]),
    height=int(size[1]),
    quality=quality,
    data=str(base64.b64decode(data),"utf8"),
    ext=ext
  )

  for f in os.listdir("./temp"):
    try:
      if f.startswith("temp"):os.remove("./temp/"+f)
    except:
      pass

  if format=="zip":
    archive_file="./temp/Collection.7z"
    with py7zr.SevenZipFile(archive_file, 'w') as archive:
      for f in files:
        archive.write(f)

    for f in files:
      os.remove(f)

    return send_file(archive_file,attachment_filename="Collection.7z")

  if format=="list":
    return files

  if format=="upload":
    platform=request.args.get("platform","ipfs")
    for f in files:
      upload_on_platform(f,platform)

  if format=="preview":
    rc=[]
    for filename in files:
      f=open(filename,"rb")
      only_filename=filename[filename.rindex("/")+1:]
      rc.append({"src":"data:image/jpeg;base64,"+str(base64.b64encode(f.read()),"utf8"),"filename":only_filename})
      f.close()
      os.remove(filename)

    return jsonify(rc)





@app.route('/api/infos/')
#test http://127.0.0.1:4242/api/infos/
#test https://server.f80lab.com:4242/api/infos/
def infos():
  rc={"Solana":{"keys":len(Solana().get_keys(with_balance=True))},
      "Elrond":{},
      "Secret":{},
      "Database":{
        "tokens":dao.db["nfts"].find().count(True)
      }
      }
  return jsonify(rc)





@app.route('/api/get_nft_from_db/',methods=["GET"])
def get_nft_from_db():
  id=request.args.get("id")
  return jsonify(dao.get(id))



@app.route('/api/test/',methods=["GET"])
#test http://127.0.0.1:4242/api/test/
#test https://server.f80lab.com:4242/api/test
def test2():
  ps_key="SA92LXSJW9MC28NC8G933SPNZPP9MQDZ"
  _order=requests.get("http://161.97.75.165:8080/api/order_details/1?ws_key="+ps_key+"&io_format=JSON").json()
  log("Order="+str(_order))
  _product=requests.get("http://161.97.75.165:8080/api/products/"+_order["order_detail"]["product_id"]+"?ws_key=SA92LXSJW9MC28NC8G933SPNZPP9MQDZ&output_format=JSON").json()
  log("Product="+str(_product))
  return jsonify(_product)



@app.route('/api/export_to_prestashop/',methods=["GET",'POST'])
#test http://127.0.0.1:4242/api/export_to_prestashop/?root_category=1&ope=calvi22_devnet&api
def export_to_prestashop():
  """
  htag: transfer_to_prestashop
  :return:
  """
  _operation=get_operation(request.args.get("ope"))
  _store_section=_operation["store"]
  prestashop=PrestaTools(_store_section["prestashop"]["api_key"],_store_section["prestashop"]["server"],_store_section["prestashop"]["language"])
  root_category=prestashop.find_category(_store_section["prestashop"]["root_category"]["name"] or "NFTs")
  if root_category is None:
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
    nfts=[]
    for nft in request.json:
      _nft=NFT(object=nft)
      nfts.append(_nft)

  for nft in nfts:
    if "name" in nft.collection and nft.collection["name"] not in categories.keys():
      log("Traitement de la collection "+nft.collection["name"])
      ref_col=prestashop.find_category_in_collections(nft.collection["name"],_operation["collections"])
      store_col=prestashop.find_category_in_collections(nft.collection["name"],_operation["store"]["collections"])
      if ref_col is None:
        ref_col={"name":nft.collection["name"],"description":"","price":0}

      if not store_col is None: #cette collection n'est pas dans les collections à inclure dans la boutique
        c=prestashop.find_category(nft.collection["name"])
        if c is None:
          c=prestashop.add_category(
            ref_col["name"],
            root_category["id"],
            ref_col["description"]
          )

        categories[c["name"]]={
          "price":store_col["price"] if "price" in store_col else ref_col["price"],
          "name":ref_col["name"],
          "id":c["id"]
        }


  for nft in nfts:
    if nft.collection["name"] in categories.keys():

      features={
        "address":nft.address,
        "network":nft.network,
        "operation":_operation["id"],
        "miner":_operation["lazy_mining"]["miner"],
        "owner":nft.owner,
        "royalties":str(nft.royalties),
        "visual":nft.visual,
        "creators":" ".join([_c["address"]+"_"+str(_c["share"]) for _c in nft.creators])
      }

      product=prestashop.add_product(nft=nft,on_sale=True,
                                     operation_id=_operation["id"],
                                     features=features,
                                     tags=["NFT"]
                                     )
      if product is None:
        return returnError("Impossible de créer "+nft.toString())
      else:
        prestashop.set_product_quantity(product,nft.get_quantity())
        try:
          buf_image=convert_to_gif(nft.visual,filename="image.gif")
          image=prestashop.add_image(product["id"],"./temp/image.gif")
        except:
          log("Impossible de convertire l'image")


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


def get_operation(name:str):
  if name.startswith("b64:"): name=str(base64.b64decode(name.split("b64:")[1]),"utf8")
  if name.startswith("http"):
    rc=requests.get(name).text
    rc=yaml.load(rc,Loader=yaml.FullLoader)
  else:
    name=name.replace(".yaml","")
    rc=yaml.load(open("./Operations/"+name+".yaml","r"),Loader=yaml.FullLoader)
  return rc




@app.route('/api/transfer_to/<nft_addr>/<to>/<owner>',methods=["GET"])
def transfer_to(nft_addr:str,to:str,owner:str):
  network=request.args.get("network","solana-devnet")
  solana=Solana(network)
  if "@" in to:
    words,to,secret_key,secret_key_ints=solana.create_account(to,domain_appli=app.config["DOMAIN_APPLI"],network=network)
  if solana.transfer(nft_addr,to,owner):
    return jsonify({"error":"","message":"NFT transféré"})
  else:
    return jsonify({"error":"Le serveur ne dispose pas de la clé du propriétaire pour effectuer le transfert"})


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



def get_access_code_from_email(email:str):
  return hashlib.md5((email+SALT).encode()).hexdigest().upper()[:6]


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
      for user in rc["validate"]["users"]:
        rc["validate"]["access_codes"].append(get_access_code_from_email(user))


  if request.method=="POST":
    with open("./Operations/"+request.json["filename"],"w") as file:
      file.write(str(base64.b64decode(request.json["file"].split("base64,")[1]),"utf8"))
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
    if ope.startswith("http"):
      rc=yaml.load(ope,Loader=yaml.FullLoader)
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


def get_nfts_from_src(srcs,collections=None,limit=10000,with_attributes=False) -> list[NFT]:
  """
  Récupération des NFTS depuis différentes sources (#getnftfromsrc)
  :param srcs:
  :param collections:
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
          if collections:
            for collection in collections:
              l_nfts=list(DAO(src["connexion"],src["dbname"]).nfts_from_collection(collection,True))
              nfts=nfts+l_nfts[:src["filter"]["limit"]]
              src["ntokens"]=len(l_nfts)
          else:
            l_nfts=list(DAO(src["connexion"],src["dbname"]).nfts_from_collection(None,False))
            nfts=nfts+l_nfts[:src["filter"]["limit"]]

          src["ntokens"]=len(l_nfts)
        except:
          log("Probleme de lecture de "+src["connexion"])

      if src["type"]=="web":
        #TODO: a terminer
        if src["connexion"].startswith("http"):
          r=requests.get(src["connexion"])
          if src["connexion"].endswith(".json"):nfts=nfts+json.loads(r.text)
          if src["connexion"].endswith(".yaml"):nfts=nfts+yaml.load(r.text,Loader=yaml.FullLoader)

      if src["type"]=="json":
        try:
          nfts=nfts+json.load(open(src["connexion"]))
        except:
          log("Probleme de lecture de "+src["connexion"])

      if src["type"]=="network":
        if src["connexion"].startswith("solana"):
          l_nfts=Solana(src['connexion']).get_nfts(src["owner"],limit=src["filter"]["limit"])
          nfts=nfts+l_nfts
          src["ntokens"]=len(l_nfts)

        if src["connexion"].startswith("elrond"):
          elrond=Elrond(src['connexion'])
          nfts=elrond.get_nfts(src["owner"],limit=src["filter"]["limit"],with_attr=with_attributes)
          src["ntokens"]=len(nfts)

      if src["type"]=="config":
        config=configs(src["connexion"],format="dict")
        for layer in config["layers"]: layers(layer)

        files=get_collection(
          size=(config["width"],config["height"]),
          format="list",
          seed=src["seed"] if "seed" in src else 1,
          limit=src["limit"] if "limit" in src else 10
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






@app.route('/api/get_tokens_to_send/<ope>',methods=["GET"])
#test http://127.0.0.1:4242/api/get_tokens_for_dispenser/calvi22_devnet?limit=10
def get_tokens_to_send(ope:str):
  section=request.args.get("section","dispenser")
  _opes=open_operation(ope)
  if _opes is None:return jsonify({"error":"operation unknown"})

  limit=int(request.args.get("limit","100000"))
  nfts=get_nfts_from_src(_opes["data"]["sources"],_opes[section]["collections"],limit=limit)
  if limit>0 and len(nfts)>limit: nfts=nfts[:limit]

  return jsonify(nfts)


@app.route('/api/key/<code>',methods=["GET"])
def get_key(code):
  format=request.args.get("format","qrcode")
  scale=request.args.get("scale",9)

  buffer=BytesIO()
  pyqrcode.create(code).png(buffer,scale=scale)

  if format=="qrcode":
    response = make_response(buffer.getvalue())
    response.headers.set('Content-Type', 'image/png')
    return response







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
  nfts=get_nfts_from_src(_opes["data"]["sources"],lottery["collections"],with_attributes=True)
  if len(nfts)==0:
    log("Aucun NFT n'est disponible")
    return "Aucun NFT",404

  #vérification de la possibilité d'emettre
  rc=DAO(ope=_opes).db["histo"].aggregate([{"$match":{"command":"mint"}},{"$group":{"_id":"$operation","count": { "$sum": 1 }}}])
  for e in rc:
    if e["_id"]==_opes["id"]:
      if "limits" in lottery and lottery["limits"]["by_year"]<e["count"]:
        nfts=[]


  if not "dtStart" in lottery or lottery["dtStart"]=="now":
    nft=None
    while True:
      nft=nfts[int(random()*len(nfts))]
      if nft["quantity"]>0:break

    visual=nft["image"] if "image" in nft and lottery["screen"]["showVisual"] else ""

    url=str(base64.b64decode(url_appli),"utf8")+"/dm/?toolbar=false&id="+nft["id"]+"&ope="+_opes["id"]

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
    nfts=get_nfts_from_src(_ope["data"]["sources"],False)

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

  log("Chargement de l'opération "+_p["reference"])
  _operation=get_operation(_p["reference"].split(" / ")[0])

  prestashop=PrestaTools(_operation["store"]["prestashop"]["api_key"],_operation["store"]["prestashop"]["server"])
  _p=prestashop.get_products(_p["id_product"])
  _c=prestashop.get_categories(int(_p["associations"]["categories"][0]["id"]))

  for feature in _p["associations"]["product_features"]:
    obj=prestashop.get_product_feature(feature["id"],feature["id_feature_value"])
    _p[obj[0]]=obj[1]

  collection=_c["name"]
  id_image=_p["associations"]["images"][0]["id"]
  miner=body["miner"] if "miner" in body else _operation["lazy_mining"]["miner"]

  visual=_p["visual"] if "visual" in _p else _operation["store"]["prestashop"]["server"]+"api/images/products/"+id_image+"/"+id_image+"?ws_key="+_operation["store"]["prestashop"]["api_key"]

  if not "network" in _p:_p["network"]=_operation["lazy_mining"]["network"]
  addresses=dict()
  if "address" in body and not body["address"] is None:
    addresses=yaml.load(body["address"]) or dict()

  attributes=prestashop.desc_to_dict(_p["description"])

  if "elrond" in _p["network"]:
    elrond=Elrond(_p["network"])
    royalties=body["royalties"] if "royalties" in body else 0

    if not "elrond" in addresses:
      _account,pem,words,qrcode=elrond.create_account(email=body["email"],domain_appli=app.config["DOMAIN_APPLI"])
      addresses["elrond"]=_account.address.bech32()
      prestashop.edit_customer(body["customer"],"note",yaml.dump(addresses))
    else:
      _account=elrond.toAccount(addresses["elrond"])


    if not "address" in _p or _p["address"] is None or _p["address"]=="":
      collection_id=elrond.add_collection(miner,collection,type="NonFungible")
      nonce,cid=elrond.mint(miner,_p["name"],collection_id,attributes,IPFS(IPFS_SERVER),[],body["quantity"],royalties,visual)
      t=elrond.transfer(collection_id,nonce,miner,_account)
    else:
      collection_id,nonce=elrond.extract_from_tokenid(_p["address"])
      t=elrond.transfer(collection_id,nonce,_p["owner"],_account)


    account_addr=_account.address.bech32()
    if t is None:
      return returnError("Impossible de transférer le NFT",{"address":_account.address.bech32()})

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

  id=body["tokenid"]
  account=body["account"]
  network=body["network"]
  miner=body["miner"]
  metadata_storage=body["metadata_storage"]

  _ope=open_operation(body["ope"])
  if _ope is None:
    _data=body["token"]
  else:
    _data=None
    nfts=get_nfts_from_src(_ope["data"]["sources"],with_attributes=True)
    for nft in nfts:
      if nft["id"]==id and nft["quantity"]>0:
        _data=nft
    if _data is None: return jsonify({"error":"Ce NFT n'est plus disponible"})


  if is_email(account):
    email=body["account"]
    if "elrond" in network:
      elrond=Elrond(network)
      _account,pem,words,qrcode=elrond.create_account(domain_appli=app.config["DOMAIN_APPLI"])
      account=_account.address.bech32()
      log("Notification de "+body["account"]+" que son compte "+elrond.getExplorer(account,"account")+" est disponible")
      send_mail(open_html_file("mail_new_account_withnft",{
        "wallet_address":account,
        "mini_wallet":"wallet?"+setParams({"toolbar":"false","network":network,"addr":account}),
        "nft_name":_data["name"],
        "url_wallet":"https://wallet.elrond.com" if "mainnet" in network else "https://devnet-wallet.elrond.com",
        "words":words,
        "qrcode":"cid:qrcode"
      },domain_appli=app.config["DOMAIN_APPLI"]),email,subject="Votre NFT '"+_data["name"]+"' est disponible" ,attach=qrcode,filename="qrcode.png")
    else:
      solana=Solana(network)
      words,pubkey,privkey,list_int=solana.create_account(domain_appli=app.config["DOMAIN_APPLI"],network=network)
      send_mail(open_html_file("mail_new_solana_account_withnft",{
        "wallet_address":pubkey, #_account.public_key.to_base58(),
        "mini_wallet":"wallet?"+setParams({"toolbar":"false","network":network,"addr":pubkey}),
        "nft_name":_data["name"],
        "words":words,
        "private_key":privkey, #_account.secret_key.hex(),
        #"private_key_in_list":str([int(x) for x in _account.secret_key])
      },domain_appli=app.config["DOMAIN_APPLI"]),email,subject="Votre NFT '"+_data["name"]+"' est disponible")
      account=pubkey

    if not _ope is None:
      dao.add_histo(_ope["id"],"new_account",account,"","",_ope["network"],"Création d'un compte pour "+body["account"],[body["account"]])

  tx=""
  if account.startswith("erd"):
    elrond=Elrond(network)
    collection_id=elrond.add_collection(miner,_data["collection"]["name"],type="NonFungible")
    solde=elrond.get_account(miner)["amount"]
    nonce,cid=elrond.mint(miner,
                          title=_data["name"],
                          collection=collection_id,
                          properties=elrond.format_offchain(_data)["properties"],
                          files=elrond.format_offchain(_data)["files"],
                          ipfs=Infura(), #IPFS(IPFS_SERVER,IPFS_PORT),
                          quantity=1,
                          royalties=20,
                          visual=_data["image"]
                          )

    if nonce:
      token_id=collection_id+"-"+nonce
      dao.delete(id)
      if miner!=account:
        rc=elrond.transfer(collection_id,nonce,miner,account)

      cost=elrond.get_account(miner)["amount"]-solde
      log("Cout de l'operation "+str(cost)+" egld")

      rc={"command":"ESDTCreate",
          "error":"",
          "link":elrond.getExplorer(token_id,"nfts"),
          "out":"",
          "ope":_ope,
          "cost":cost,
          "result":{
            "transaction":token_id,
            "mint":token_id
          },
          "unity":"EGLD",
          "link_transaction":elrond.getExplorer(token_id,"nfts"),
          "link_mint":elrond.getExplorer(token_id,"nfts"),
          "wallet_link":"https://devnet-wallet.elrond.com/unlock/pem"
          }
      tx=token_id
    else:
      rc={}

  else:
    solana=Solana("solana-"+body["type_network"])
    if not "uri" in _data or len(_data["uri"])==0:
      _data["uri"]=upload_on_platform(solana.prepare_offchain_data(_data),metadata_storage)["url"]
    rc=solana.mint(_data,miner=miner,sign=True,owner=account)
    if len(rc["error"])>0:
      return jsonify({"error":rc["error"]})

    if _ope: rc["ope"]=_ope["id"]

  collection_name=_data["collection"]["name"] if "collection" in _data else nft["collection"]["name"]
  if len(rc["error"])==0:
    if not _ope is None:
      dao.add_histo(_ope["id"],"mint",account,collection_name,rc["result"]["transaction"],_ope["network"],"minage pour loterie")

    _data["quantity"]=_data["quantity"]-1
    DAO(_data["domain"],_data["dbname"]).update(_data,"quantity")

  return jsonify(rc)



@app.route('/api/apply_filter/',methods=["POST"])
def apply_filter():
  body=request.json
  l=nft.get_layer(body["layer"])
  if l is None: return jsonify({"error":"layer unknonw"})

  rc=l.apply_filter(body["filter"])
  return jsonify({"error":"","images":rc})





@app.route('/api/save_config/<name>/',methods=["POST"])
def save_config(name:str):
  log("Demande d'enregistrement de la config "+name)

  filename="./Configs/"+name+(".yaml" if not name.endswith(".yaml") else "")
  log("Ouverture en ecriture du fichier de destination "+filename)

  s=str(yaml.dump(request.json,Dumper=Dumper,default_flow_style=False,indent=4,encoding="utf8"),"utf8")
  f=open(filename,"w")
  f.writelines(s)
  f.close()

  log("Fermeture du fichier")

  return jsonify({"error":"","content":str(request.data,"utf8")})




@app.route('/api/configs/<name>/',methods=["GET","DELETE"])
@app.route('/api/configs/')
#test http://127.0.0.1:4242/api/infos/
#test https://server.f80lab.com:4242/api/infos/
def configs(name:str="",format=""):
  if len(name)==0:
    return jsonify({"files":os.listdir("./Configs")})
  else:
    if request.method=="GET":
      if len(format)==0: format=request.args.get("format","yaml")
      filename="./Configs/"+name.replace(".yaml","")+".yaml"
      rc=dict()
      if exists(filename):
        with open(filename,"r") as file:
          rc=yaml.load(file,Loader=yaml.FullLoader)

      if format=="json": return jsonify(rc)
      if format=="dict": return rc

      return send_file(path_or_file=filename,mimetype="plain/text",as_attachment=True,download_name=name+("" if name.endswith(".yaml") else ".yaml"))
    else:
      if request.method=="DELETE":
        os.remove("./Configs/"+name)
      return jsonify({"error":""})




@app.route('/api/ftx/tokens/',methods=["GET"])
@app.route('/api/ftx/nfts/',methods=["GET"])
#test http://127.0.0.1:4242/api/ftx/tokens/?key=solMintAddress&value=!none&out=solMintAddress,description,id
#test https://server.f80lab.com:4242/api/ftx/tokens/?key=solMintAddress&value=!none&out=solMintAddress,description,id
def ftx_tokens():
  key=request.args.get("key","solMintAddress")
  value=request.args.get("value","!none")
  out=request.args.get("out","")
  rc=ftx.nfts("nfts",key,value,out,timeout=int(request.args.get("timeout","0")))
  if rc["status_code"]==200:
    log(str(len(rc))+" NFTs trouvés")

  return jsonify(rc)



@app.route('/api/ftx/collections/',methods=["GET"])
#test http://127.0.0.1:4242/api/ftx/collections/
#test https://server.f80lab.com:4242/api/ftx_tokens/
def ftx_collections():
  filter=request.args.get("filter","")
  rc=ftx.collections(filter)
  return jsonify(rc)


@app.route('/api/ftx/account/',methods=["GET"])
#test http://127.0.0.1:4242/api/ftx/account/
def ftx_account():
  rc=ftx.account()
  return jsonify(rc)





@app.route('/api/keys/',methods=["GET"])
@app.route('/api/keys/<name>/',methods=["DELETE","POST"])
#https://metaboss.rs/set.html
#test http://127.0.0.1:9999/api/keys/
#test https://server.f80lab.com:4242/api/keys/
def keys(name:str=""):
  network=request.args.get("network","solana-devnet").lower()

  if request.method=="GET":
    if "elrond" in network:
      return jsonify(Elrond(network).get_keys(with_qrcode=True))
    if "solana" in network:
      rc=Solana(network).get_keys(with_private=(request.args.get("with_private","false")=="true"),with_balance=True,with_qrcode=True)
      return jsonify(rc)

  filename=(SOLANA_KEY_DIR+name+".json").replace(".json.json",".json") if "solana" in network else (ELROND_KEY_DIR+name+".pem").replace(".pem.pem",".pem")
  if request.method=="DELETE":
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
        _u,key,words,qrcode=Elrond(network).create_account(email,network,domain_appli=app.config["DOMAIN_APPLI"])

    f = open(filename, "w")
    f.write(key)
    f.close()

  return jsonify({"message":"ok"})



@app.route('/api/refill/',methods=["GET"])
#https://metaboss.rs/mint.html
def refill():
  addr=request.args.get("addr","")


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
@app.route('/api/images/<cid>',methods=["GET","DELETE"])
@app.route('/api/images/',methods=["GET","DELETE"])
def get_image(cid:str=""):
  if request.method=="GET":
    if len(cid)==0:
      return jsonify({"files":os.listdir("./temp")})
    else:
      f=open("./temp/"+cid,"r" if cid.endswith(".svg") else "rb")
      format="image/svg+xml" if cid.endswith(".svg") else "image/webp"
      response = make_response(f.read())
      response.headers.set('Content-Type', format)
      return response

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



def upload_on_platform(data,platform="ipfs",id=None,options={}):
  if platform=="ipfs":
    ipfs=IPFS(IPFS_SERVER)
    cid=ipfs.add(data,removeFile=True)
    rc={"cid":cid["Hash"],"url":ipfs.get_link(cid["Hash"])+("?"+cid["Name"] if "Name" in cid else "")}

  if platform=="infura":
    infura=Infura()
    cid=infura.add(data)
    rc={"cid":cid["Hash"],"url":cid["url"]}

  if platform=="mongodb":
    cid=dao.add_dict(data)
    rc={"cid":cid,"url":app.config["DOMAIN_APPLI"]+"/api/json/"+cid}

  if platform.startswith("nfluent"):
    b=base64.b64decode(data["content"].split("base64,")[1])
    ext=data["type"].split("/")[1].split("+")[0]
    if ext=="gif" or ext=="png": ext="webp"
    cid=hex(hash(data["content"]))+"."+ext
    filename="./temp/"+cid

    if ext=="svg":
      s=Sticker(cid,text=str(base64.b64decode(data["content"].split("base64,")[1]),"utf8"))
    else:
      s=Sticker(cid,data["content"])

    s.save(filename)

    rc={"cid":cid,"url":app.config["DOMAIN_SERVER"]+"/api/images/"+cid+"?format="+data["type"]}

  if platform=="nftstorage":
    if "content" in data:
      rc=NFTStorage().add(data["content"],data["type"],data["filename"])
    else:
      rc=NFTStorage().add(data)

  if platform=="googlecloud":
    rc=GoogleCloudStorageTools().add(data,id)

  if platform.startswith("github"):
    repo=options["repository"] if "repository" in options else platform.split("/")[1].strip()
    github_storage=GitHubStorage.GithubStorage(repo,"main","nfluentdev",GITHUB_TOKEN)
    rc= github_storage.add(data,id,overwrite=False)

  return rc


#https://server.f80lab.com:4242/api/nfts/
#http://127.0.0.1:4242/api/nfts/
@app.route('/api/nfts/',methods=["GET"])
def nfts():
  network=request.args.get("network","solana-devnet")
  account=request.args.get("account","paul").lower()
  with_attr="with_attr" in request.args
  limit=request.args.get("limit","200")
  rc=[]
  if "elrond" in network:
    rc=rc+Elrond(network).get_nfts(account,int(limit),with_attr=with_attr)
  else:
    rc=rc+Solana(network).get_nfts(account)
  return jsonify(rc)




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


from cryptography.fernet import Fernet
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
      access_code=get_access_code_from_email(validateur)
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





@app.route('/api/upload/',methods=["POST"])
def upload():
  """
  Chargement des fichiers
  :return:
  """
  platform=request.args.get("platform","ipfs")
  if str(request.data,"utf8").startswith("{"):
    body=request.json
  else:
    content=str(request.data,"utf8")
    if not "base64" in content:content=";base64,"+content
    body={
      "filename":request.args.get("filename","temp"),
      "content":content,
      "type":request.args.get("type","")
    }

  if body["type"]=="":
    if "filename" in body and body["filename"].startswith("qrcode:"):
      body["type"]="image/png"

      qr=pyqrcode.create(body["filename"].split("qrcode:")[1])
      buffered = BytesIO()
      qr.png(buffered,scale=3)

      body["content"]=";base64,"+str(base64.b64encode(buffered.getvalue()),"utf8")
      body["filename"]="qrcode.png"

    else:
      if body["filename"].endswith(".mp4") or body["filename"].endswith(".avi") or body["filename"].endswith(".webm"):
        body["type"]="video/"+body["filename"]
      else:
        body["type"]="image/"+body["filename"].split(".")[1]

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




@app.route('/api/mint/',methods=["POST"])
def mint():
  """
  Minage des NFT sur les différents réseaux possibles : elrond, solana, base de donnée, fichier json
  :return:
  """
  keyfile=request.args.get("keyfile","paul").lower()
  network=request.args.get("network","solana-devnet")
  offchaindata_platform=request.args.get("offchaindata_platform","ipfs").replace(" ","").lower()
  _data=request.json
  if _data is None:
    text=str(request.data,"utf8").replace('\x00','')
    _data=json.loads(text)

  if _data is None:
    s=str(request.data,"utf8")
    for i in range(200): s=s.replace("\r\n","")
    _data=json.loads(s)

  if not _data["image"].startswith("http"):
    return jsonify({"error":"Vous devez uploader les images avant le minage"})

  log("Minage avec les metadata "+str(_data))
  collection_id=_data["collection"]["name"] if "collection" in _data else ""

  if "elrond" in network.lower():
    elrond=Elrond(network)
    collection_id=elrond.add_collection(keyfile,_data["collection"]["name"],type="NonFungible")
    nonce,cid=elrond.mint(keyfile,
                          title=_data["name"],
                          collection=collection_id,
                          properties=elrond.format_offchain(_data)["properties"],
                          files=elrond.format_offchain(_data)["files"],
                          ipfs=IPFS(IPFS_SERVER),
                          quantity=1,
                          royalties=_data["seller_fee_basis_points"]/100,  #On ne prend les royalties que pour le premier créator
                          visual=_data["image"]
                          )

    if nonce is None:
      rc={"error":"Probleme de création"}
    else:
      _data["uri"]=cid["url"]
      infos=elrond.get_account(keyfile)
      token_id=collection_id+"-"+nonce
      rc={"command":"ESDTCreate",
          "error":"",
          "link":elrond.getExplorer(token_id,"nfts"),
          "uri":_data["uri"],
          "out":"",
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
    _data["uri"]=upload_on_platform(solana.prepare_offchain_data(_data),offchaindata_platform,
                                    id=request.args.get("filename_for_metadata",None),
                                    options={"repository":request.args.get("repository","calviontherock")},
                                    )["url"]
    #voir https://metaboss.rs/mint.html
    #(request.args.get("sign","True")=="True" or request.args.get("sign","all")=="all")
    rc=solana.mint(_data,miner=keyfile,sign=False,owner=request.args.get("owner",""))

    if request.args.get("sign_all","False")=="True" and "result" in rc and "mint" in rc["result"]:
      signers=[x["address"] for x in _data["creators"]]
      #signers.remove(solana.find_address_from_json(keyfile))
      solana.sign(rc["result"]["mint"],signers)

  if "database" in network.lower():
    db_loc=request.args.get("db_loc","cloud")
    db_name=request.args.get("db_name","nfts")
    rc=DAO(db_loc,db_name).lazy_mint(_data,"",app.config["APPLICATION_ROOT"])

  if "jsonfiles" in network.lower():
    filename=_data["name"]+"_"+_data["symbol"]+"_"+_data["collection"]["name"]+".json"
    with open("./temp/"+filename,"w") as f:
      json.dump(_data,f,indent=4)
    rc={
      "error":"",
      "uri":_data["uri"],
      "result":{"transaction":"","mint":filename},
      "balance":0,
      "link_mint":"",
      "link_transaction":"",
      "out":"",
      "command":"file"
    }

  if "result" in rc and "transaction" in rc["result"]:
    dao.add_histo(request.args.get("ope",""),"mint",keyfile,collection_id,rc["result"]["transaction"],network,"Minage")
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
  with ZipFile('./Temp/archive.zip', 'w') as myzip:
    for token in request.json:
      file_to_mint="./Temp/"+str(i)+".json"
      with open(file_to_mint, 'w') as f:
        f.writelines(json.dumps(token,indent=4, sort_keys=True))
        f.close()

      myzip.write(file_to_mint)
      i=i+1

    myzip.close()
  cid=ipfs.add_file('./Temp/archive.zip')
  return jsonify({"zip_file":ipfs.get_link(cid)})








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


  CORS(app)

  app.config.from_mapping({
    "DEBUG": True,                    # some Flask specific configs
    "CACHE_TYPE": "SimpleCache",      # Flask-Caching related configs
    "CACHE_DEFAULT_TIMEOUT": 300,
    "APPLICATION_ROOT":sys.argv[2],
    "DOMAIN_APPLI":sys.argv[2],
    "DOMAIN_SERVER":sys.argv[1],
    "UPDLOAD_FOLDER":"./Temp/"
  })

  _port=int(app.config["DOMAIN_SERVER"].split(":")[2])

  if "debug" in sys.argv:
    app.run(debug=True,port=_port)
  else:
    if "ssl" in sys.argv:
      app.config.update(SESSION_COOKIE_SECURE=True,SESSION_COOKIE_HTTPONLY=True,SESSION_COOKIE_SAMESITE='Lax')

      context = ssl.SSLContext(ssl.PROTOCOL_TLSv1_2)
      context.load_cert_chain("/certs/fullchain.pem", "/certs/privkey.pem")
      app.run(debug=False,port=_port,ssl_context=context,host="0.0.0.0")
    else:
      app.run(debug=False,port=_port,host="0.0.0.0")






