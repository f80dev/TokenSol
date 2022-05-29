import base64
import csv
import datetime
import hashlib
import json
import os
import ssl
import sys

from io import BytesIO
from random import random
from time import sleep

from zipfile import ZipFile

import py7zr
import pyqrcode
import requests
import yaml

from flask import request, jsonify, send_file, Flask, make_response
from flask_cors import CORS
from fontTools import ttLib

from werkzeug.datastructures import FileStorage
from yaml import dump

import GitHubStorage
from ArtEngine import ArtEngine, Layer, Sticker, TextElement
from Elrond.Elrond import Elrond
from GoogleCloudStorageTools import GoogleCloudStorageTools
from dao import DAO
from ftx import FTX
from Solana.Solana import SOLANA_KEY_DIR, Solana
from Tools import hex_to_str, log, filetype, now, is_email, send_mail, open_html_file
from infura import Infura
from ipfs import IPFS
from nftstorage import NFTStorage
from secret import GITHUB_TOKEN, SALT

app = Flask(__name__)
ftx=FTX()
nft=ArtEngine()
dao=DAO("cloud","CalviOnTheRock")


#voir la documentation de metaboss:

IPFS_PORT=5001
IPFS_SERVER="/ip4/161.97.75.165/tcp/"+str(IPFS_PORT)+"/http"


#http://127.0.0.1:9999/api/update/?account=GwCtQjSZj3CSNRbHVVJ7MqJHcMBGJJ9eHSyxL9X1yAXy&url=
#TODO: ajouter les restrictions d'appel
@app.route('/api/update/')
#https://metaboss.rs/set.html
def update():
  url=request.args.get("url")
  account=request.args.get("account")
  return exec("update","uri --new-uri "+url,account=account)


@app.route('/api/test/')
#test http://127.0.0.1:4242/api/test/
def test():
  solana=Solana()
  _acc=solana.find_address_from_json(request.args.get("addr","paul"))
  tokens=solana.get_nfts(_acc)
  token=tokens[0]
  infos=solana.get_infos(token["account"]["data"]["parsed"]["info"]["mint"])
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
def layers():
  name=request.json["name"]
  log("Generation de la couche "+name)
  nft.delete(name) # <-- cette instance ne devrait plus être partagés dans une optique multi-usage
  position=request.json["position"] if "position" in request.json else 0
  layer=Layer(name,
              position=position,
              unique=(request.json["unique"] if "unique" in request.json else False),
              indexed=(request.json["indexed"] if "indexed" in request.json else True)
  )
  s=None
  if "files" in request.json:
    log("Remplissage des calques")
    for f in request.json["files"]:
      if filetype(f)=="text":
        s=TextElement(request.json["text"])
      else:
        log("Ajout de "+f)
        s=Sticker("",image=f,dimension=(request.json["width"],request.json["height"]))

      layer.add(s)
  else:
    if "text" in request.json and len(request.json["text"])>0:
      for txt in request.json["text"].split("|"):
        if len(txt)>0:
          s=Sticker(name=txt,text=txt,x=request.json["x"],y=request.json["y"],
                    dimension=(request.json["width"],request.json["height"]),
                    fontstyle=request.json["fontstyle"])
          layer.add(s)

  log("Fin de generation de "+layer.name)
  nft.add(layer)
  if s:
    return jsonify({"status":200,"images":[s.toBase64() for s in layer.elements]})
  else:
    return jsonify({"status":200})



@app.route('/api/collection/')
#test http://127.0.0.1:4242/api/test/
def get_collection():
  limit=int(request.args.get("limit",10))
  size=request.args.get("size","500,500").split(",")
  format=request.args.get("format","zip")
  ext=request.args.get("image","webp")
  nft.name=request.args.get("name","mycollection").replace(".png","")

  collage=Sticker("collage",dimension=(int(size[0]),int(size[1])),ext=ext)
  files=nft.generate(collage,"./temp/",limit)

  if format=="zip":
    archive_file="./temp/Collection.7z"
    with py7zr.SevenZipFile(archive_file, 'w') as archive:
      for f in files:
        archive.write(f)

    for f in files:
      os.remove(f)

    return send_file(archive_file,attachment_filename="Collection.7z")


  if format=="upload":
    platform=request.args.get("platform","ipfs")
    for f in files:
      upload_on_platform(f,platform)


  if format=="preview":
    rc=[]
    index=0
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
  rc={"Solana":{"keys":len(Solana().get_keys())},
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
        if type(row[k])==dict:
          row[k]=str(row[k])

      rc.append(row)

  if request.method=="DELETE":
    dao.db[table].drop()
    rc={"error":""}

  return jsonify(rc)



@app.route('/api/action_calvi/',methods=["POST"])
def action():
  """
  validation des NFT pour l'opération calvi
  :return:
  """
  body=request.json
  attrs=body["offchain"]["attributes"]
  nbPass=int(request.args.get("nb_pass","2"))
  for i in range(1,5):
    key="Edition"+str(i)
    for a in attrs:
      if a["trait_type"]==key and int(a["value"])>nbPass:
        a["value"]=a["value"]-nbPass
        GitHubStorage.GithubStorage("test","main","nfluentdev",GITHUB_TOKEN).add(body["offchain"],body["uri"],True)
        return jsonify({
          "error":"",
          "message":"Vous pouvez distribuer les passes"
        })


  return jsonify({"error":"Aucun passe disponible pour ce nft"})



def get_access_code_from_email(email:str):
  return hashlib.md5((email+SALT).encode()).hexdigest().upper()


@app.route('/api/operations/',methods=["GET","POST"])
@app.route('/api/operations/<ope>/',methods=["DELETE","GET"])
#test http://127.0.0.1:4242/api/operations/
#test http://127.0.0.1:4242/api/operations/calvi22
def manage_operations(ope=""):
  if request.method=="GET":
    rc=[]
    for o in os.listdir("./Operations"):
      if o.endswith("yaml"):
        with open("./Operations/"+o,"r") as file:
          _opes=yaml.load(file,Loader=yaml.FullLoader)
          _opes["validate"]["access_codes"]=[]
          for user in _opes["validate"]["users"]:
            _opes["validate"]["access_codes"].append(get_access_code_from_email(user))

          rc.append({
            "title":_opes["title"],
            "code":o,
            "content":_opes
          })
        if ope.lower()==_opes["title"].lower():
          rc=_opes
          break

  if request.method=="POST":
    with open("./Operations/"+request.json["filename"],"w") as file:
      file.write(str(base64.b64decode(request.json["file"].split("base64,")[1]),"utf8"))
    rc={"error":""}

  if request.method=="DELETE":
    os.remove("./Operations/"+ope)
    rc={"error":""}

  return jsonify(rc)



def open_operation(ope):
  rc=None
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
  for field in ["title","data","miners"]:
    if not field in rc:
      log("Le champs "+field+" est obligatoire dans une opération")
      rc=None
      break

  return rc

#test http://127.0.0.1:4242/api/get_new_code/demo?format=qrcode
#http://127.0.0.1:4242/api/get_new_code/demo/http%3A%2F%2F127.0.0.1%3A4200/
#http://127.0.0.1:4200/contest?ope=demo
@app.route('/api/get_new_code/<ope>/<url_appli>',methods=["GET"])
@app.route('/api/get_new_code/<ope>',methods=["GET"])
def get_token_for_contest(ope:str,url_appli:str="https://tokensol.nfluent.io"):
  format=request.args.get("format","json")

  _opes=open_operation(ope)

  #chargement des NFTs
  nfts=[]
  for src in _opes["data"]["nfts"]:
    if src["source"] in ["database","db"]:
      nfts=nfts+list(dao.nfts_from_collection(src["collection"]))

    if src["source"].startswith("http") and src["source"].endswith(".json"):
      r=requests.get(src["source"])
      nft=json.loads(r.text)
      nfts.append(nft)

  if len(nfts)==0:
    return "Aucun NFT",404

  if not "dtStart" in _opes or _opes["dtStart"]=="now":
    nft=nfts[int(random()*len(nfts))]
    visual=nft["image"] if "image" in nft and _opes["showVisual"] else ""
    rc=dao.mint(nft,ope)

    url=str(base64.b64decode(url_appli),"utf8")+"/dealermachine/?id="+rc["result"]["mint"]

    buffer=BytesIO()
    pyqrcode.create(url).png(buffer,scale=3)

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


  _data=dao.get(id)

  if _data is None:
    return jsonify({"error":"Ce NFT n'est plus disponible"})

  _ope=open_operation(_data["ope"])

  if is_email(account):
    elrond=Elrond("elrond_"+body["type_network"])
    _account,pem=elrond.create_account(account)
    account=_account.address.bech32()
    log("Notification de "+body["account"]+" que son compte "+elrond.getExplorer(account,"account")+" est disponible")
    send_mail(open_html_file("mail_new_account",{
      "wallet_address":account,
      "nft_name":_data["name"],
    }),body["account"],subject="Votre NFT",attach=pem)



  if account.startswith("erd"):
    elrond=Elrond("elrond_"+body["type_network"])
    collection_id=elrond.add_collection(_ope["miners"]["elrond"],_data["collection"]["name"],type="NonFungible")
    nonce=elrond.mint(_ope["miners"]["elrond"],
                      title=_data["name"],
                      collection=collection_id,
                      properties=elrond.format_offchain(_data),
                      ipfs=IPFS(IPFS_SERVER,IPFS_PORT),
                      quantity=1,
                      royalties=20,
                      visual=_data["image"]
                      )

    if nonce:
      token_id=hex_to_str(collection_id)+"-"+nonce
      dao.delete(id)
      if _ope["miners"]["elrond"]!=account:
        rc=elrond.transfer(collection_id,nonce,_ope["miners"]["elrond"],account)

      dao.add_histo(account,collection_id)
      rc={"command":"ESDTCreate",
          "error":"",
          "link":elrond.getExplorer(token_id,"nfts"),
          "out":"",
          "ope":_ope["code"],
          "result":{
            "transaction":token_id,
            "mint":token_id
          },
          "unity":"EGLD",
          "link_transaction":elrond.getExplorer(token_id,"nfts"),
          "link_mint":elrond.getExplorer(token_id,"nfts"),
          "wallet_link":"https://devnet-wallet.elrond.com/unlock/pem"
          }
    else:
      rc={}

  else:
    solana=Solana("solana-"+body["type_network"])
    offchaindata_platform=request.args.get("offchaindata_platform","ipfs")
    filename=_data["symbol"] if request.args.get("filename","symbol") else None
    _data["uri"]=upload_on_platform(solana.prepare_offchain_data(_data),offchaindata_platform)["url"]
    rc=solana.mint(_data,miner=_ope["miners"]["solana"],sign=(request.args.get("sign","False")=="True"),owner=account)
    dao.delete(id)
    rc["ope"]=_ope["code"]
    dao.add_histo(account,_data["collection"])

  return jsonify(rc)





@app.route('/api/save_config/<name>/',methods=["POST"])
def save_config(name:str):
  log("Demande d'enregistrement de la config "+name)

  filename="./Configs/"+name+(".yaml" if not name.endswith(".yaml") else "")
  log("Ouverture en ecriture du fichier de destination "+filename)

  f=open(filename,"wb")
  f.write(request.data)
  f.close()

  log("Fermeture du fichier")

  return jsonify({"error":"","content":str(request.data,"utf8")})




@app.route('/api/configs/<name>/')
@app.route('/api/configs/')
#test http://127.0.0.1:4242/api/infos/
#test https://server.f80lab.com:4242/api/infos/
def configs(name:str=""):
  if len(name)==0:
    return jsonify({"files":os.listdir("./Configs")})
  else:
    format=request.args.get("format","yaml")
    filename="./Configs/"+name.replace(".yaml","")+".yaml"
    if format=="json":
      with open(filename,"r") as file:
        rc=yaml.load(file,Loader=yaml.FullLoader)
        return jsonify(rc)
    else:
      return send_file(path_or_file=filename,mimetype="plain/text",as_attachment=True,download_name=name+("" if name.endswith(".yaml") else ".yaml"))








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



@app.route('/api/keys/',methods=["POST","GET"])
@app.route('/api/keys/<name>',methods=["DELETE"])
#https://metaboss.rs/set.html
#test http://127.0.0.1:9999/api/keys/
#test https://server.f80lab.com:4242/api/keys/
def keys(name:str=""):
  network=request.args.get("network","solana-devnet").lower()

  if request.method=="GET":
    if "elrond" in network:
      return jsonify(Elrond(network).get_keys())
    if "solana" in network:
      return jsonify(Solana().get_keys(with_private=(request.args.get("with_private","false")=="true")))

  if request.method=="DELETE":
    filename=(SOLANA_KEY_DIR+name+".json").replace(".json.json",".json")
    os.remove(filename)

  if request.method=="POST":
    obj=request.json
    filename=(SOLANA_KEY_DIR+obj["name"]+".json").replace(".json.json",".json")
    f = open(filename, "w")
    key=obj["key"]
    rc=[]

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
  rc=Solana().scan(token,network)
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
      f=open("./temp/"+cid,"rb")
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



def upload_on_platform(data,platform="ipfs",id=None,repository="calviontherock"):
  if platform=="ipfs":
    ipfs=IPFS("/ip4/161.97.75.165/tcp/5001/http",5001)
    cid=ipfs.add(data,removeFile=True)
    rc={"cid":cid["Hash"],"url":ipfs.get_link(cid["Hash"])+("?"+cid["Name"] if "Name" in cid else "")}

  if platform=="infura":
    infura=Infura()
    cid=infura.add(data)
    rc={"cid":cid,"url":infura.get_link(cid)}

  if platform=="mongodb":
    cid=dao.add_dict(data)
    rc={"cid":cid,"url":sys.argv[2]+":"+sys.argv[1]+"/api/json/"+cid}

  if platform=="nfluent":
    b=base64.b64decode(data["content"].split("base64,")[1])
    cid=hex(hash(data["content"]))+".webp"
    filename="./temp/"+cid

    s=Sticker(cid,data["content"])
    s.save(filename)

    # f=open(filename,"wb")
    # f.write(b)
    # f.close()

    rc={"cid":cid,"url":sys.argv[2]+":"+sys.argv[1]+"/api/images/"+cid+"?format="+data["type"]}

  if platform=="nftstorage":
    if "content" in data:
      rc=NFTStorage().add(data["content"],data["type"],data["filename"])
    else:
      rc=NFTStorage().add(data)

  if platform=="googlecloud":
    rc=GoogleCloudStorageTools().add(data,id)

  if platform=="github":
    rc= GitHubStorage.GithubStorage(repository,"main","nfluentdev",GITHUB_TOKEN).add(data,id)

  return rc


#https://server.f80lab.com:4242/api/nfts/
#http://127.0.0.1:4242/api/nfts/
@app.route('/api/nfts/',methods=["GET"])
def nfts():
  network=request.args.get("network","solana-devnet")
  account=request.args.get("account","paul").lower()
  limit=request.args.get("limit","30")
  rc=[]
  if "elrond" in network:
    rc=rc+Elrond(network).get_nfts(account,IPFS(IPFS_SERVER,IPFS_PORT),int(limit))
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
          nft=Solana().get_token(l["address"],network)
          if nft[_ope["to_check"]] in _ope["values"]:rc={"validity":"ok"}

  return jsonify(rc)


@app.route('/api/token_by_delegate/',methods=["GET"])
#http://127.0.0.1:4242/api/token_by_delegate/?account=LqCeF9WJWjcoTJqWp1gH9t6eYVg8vnzUCGBpNUzFbNr
def get_token_by_delegate():
  network=request.args.get("network","solana-devnet")
  account=request.args.get("account","")
  rc=Solana().get_token_by_miner(account)
  return jsonify(rc)



@app.route('/api/send_email_to_validateur/',methods=["POST"])
#http://127.0.0.1:4242/api/token_by_delegate/?account=LqCeF9WJWjcoTJqWp1gH9t6eYVg8vnzUCGBpNUzFbNr
def send_email_to_validateur():
  operation=request.json
  validate_section=operation["validate"]
  for validateur in validate_section["users"]:
    access_code=get_access_code_from_email(validateur)
    url=validate_section["application"]+"?ope="+validate_section["operation_file"]+"&user="+validateur+"&access_code="+access_code+"&toolbar=false"
    send_mail(open_html_file("mail_validateur",{
      "title":operation["title"],
      "url_appli":url,
      "access_code":access_code
    }),validateur,subject=operation["title"]+" connexion à l'application de validation")

  return jsonify({"error":""})



@app.route('/api/send_transaction_confirmation/<email>/',methods=["POST"])
def send_transaction_confirmation(email:str):
  body=request.json
  send_mail(open_html_file("transaction_confirmation",{
    "n_passes":body["n_passes"],
    "nft_url":body["nft_url"],
    "nft_title":body["nft_title"]
  }),email,subject="Utilisation de votre NFT pour obtenir votre passe")
  return jsonify({"error":""})




@app.route('/api/upload/',methods=["POST"])
#https://metaboss.rs/mint.html
def upload():
  platform=request.args.get("platform","ipfs")
  if str(request.data,"utf8").startswith("{"):
    body=request.json
  else:
    body={
      "filename":request.args.get("filename","temp"),
      "content":";base64,"+str(request.data,"utf8"),
      "type":request.args.get("type","")
    }

  if body["type"]=="":
    if body["filename"].startswith("qrcode:"):
      body["type"]="image/png"

      qr=pyqrcode.create(body["filename"].split("qrcode:")[1])
      buffered = BytesIO()
      qr.png(buffered)

      body["content"]=";base64,"+str(base64.b64encode(buffered.getvalue()),"utf8")
      body["filename"]="qrcode.png"

    else:
      if body["filename"].endswith(".mp4") or body["filename"].endswith(".avi") or body["filename"].endswith(".webm"):
        body["type"]="video/"+body["filename"]
      else:
        body["type"]="image/"+body["filename"]

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



@app.route('/api/mint/',methods=["POST"])
def mint():
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


  if "elrond" in network:
    elrond=Elrond(network)
    collection_id=elrond.add_collection(keyfile,_data["collection"]["name"],type="NonFungible")
    nonce=elrond.mint(keyfile,
                   title=_data["name"],
                   collection=collection_id,
                   properties=elrond.format_offchain(_data),
                   ipfs=IPFS(IPFS_SERVER,IPFS_PORT),
                   quantity=1,
                   royalties=20,
                   visual=_data["image"]
                   )

    if nonce is None:
      rc={"error":"Probleme de création"}
    else:
      infos=elrond.get_account(keyfile)
      token_id=hex_to_str(collection_id)+"-"+nonce
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

  if "solana" in network:
    solana=Solana(network)
    _data["uri"]=upload_on_platform(solana.prepare_offchain_data(_data),offchaindata_platform,
                                    id=request.args.get("filename_for_metadata",None),
                                    repository=request.args.get("repository","calviontherock"),
                                    )["url"]
    #voir https://metaboss.rs/mint.html
    rc=solana.mint(_data,miner=keyfile,sign=(request.args.get("sign","False")=="True"),owner=request.args.get("owner",""))
    if request.args.get("sign_all","False")=="True":
      solana.sign(rc["result"]["mint"],[x["address"] for x in _data["creators"]])

  if "database" in network:
    rc=dao.mint(_data,"",app.config["APPLICATION_ROOT"])

  if "jsonfiles" in network:
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
  ipfs=IPFS("/ip4/161.97.75.165/tcp/5001/http",5001)
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
  ipfs=IPFS("/ip4/161.97.75.165/tcp/5001/http",5001)
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
  _port=int(sys.argv[1])

  CORS(app)

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

  app.config.from_mapping({
    "DEBUG": True,          # some Flask specific configs
    "CACHE_TYPE": "SimpleCache",  # Flask-Caching related configs
    "CACHE_DEFAULT_TIMEOUT": 300,
    "APPLICATION_ROOT":sys.argv[2],
    "UPDLOAD_FOLDER":"./Temp/"
  })




