import base64
import datetime
import json
import os
import ssl
import sys

from zipfile import ZipFile

import py7zr
from erdpy.accounts import Account

from flask import Response, request, jsonify, send_file, Flask
from flask_cors import CORS

from werkzeug.datastructures import FileStorage
from yaml import dump, load

from ArtEngine import ArtEngine, Layer, Sticker, TextElement
from Elrond.Elrond import Elrond
from ftx import FTX
from Solana.Solana import SOLANA_KEY_DIR, Solana
from Tools import str_to_hex, hex_to_str, log, filetype
from infura import Infura
from ipfs import IPFS
from nftstorage import NFTStorage

app = Flask(__name__)
ftx=FTX()
nft=ArtEngine()

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
  engine=ArtEngine("collage")
  for k in range(4):
    layer=Layer("layer"+str(k))
    for i in range(5):
      layer.add(TextElement("elt_"+str(k)+str(i),"L"+str(k)+"E"+str(i)))

    engine.add(layer)

  rc=engine.generate(TextElement(),limit=10)
  print(rc)
  pass


@app.route('/api/reset_collection/',methods=["GET"])
#test http://127.0.0.1:4242/api/test/
def reset_collection():
  nft.reset()
  return jsonify({"status":200})


@app.route('/api/fonts/',methods=["GET"])
#test http://127.0.0.1:4242/api/test/
def get_fonts():
  return jsonify({"fonts":os.listdir("./Fonts")})



@app.route('/api/layers/',methods=["POST"])
#test http://127.0.0.1:4242/api/test/
def layers():
  name=request.json["name"]
  nft.delete(name)
  position=request.json["position"] if "position" in request.json else 0
  layer=Layer(name,
              position=position,
              unique=(request.json["unique"] if "unique" in request.json else False),
              indexed=(request.json["indexed"] if "indexed" in request.json else True)
  )
  s=None
  if "files" in request.json:
    for f in request.json["files"]:
      if filetype(f)=="image": s=Sticker("",image=f,dimension=(request.json["width"],request.json["height"]))
      if filetype(f)=="text":s=TextElement(request.json["text"])
      layer.add(s)
  else:
    if "text" in request.json and len(request.json["text"])>0:
      for txt in request.json["text"].split("|"):
        if len(txt)>0:
          s=Sticker(name=txt,text=txt,x=request.json["x"],y=request.json["y"],
                    dimension=(request.json["width"],request.json["height"]),
                    fontstyle=request.json["fontstyle"])
          layer.add(s)

  nft.add(layer)
  if s:
    return jsonify({"status":200,"images":[s.toBase64() for s in layer.elements]})
  else:
    return jsonify({"status":200})


@app.route('/api/collection/')
#test http://127.0.0.1:4242/api/test/
def get_collection():
  limit=int(request.args.get("limit",10))
  format=request.args.get("format","zip")
  nft.name=request.args.get("name","mycollection").replace(".png","")
  collage=Sticker("collage",dimension=(500,500))
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
  rc={"Solana":
        {"keys":len(Solana().get_keys())},
      "Elrond":{},
      "Secret":{}
      }
  return jsonify(rc)


@app.route('/api/save_config/<name>/',methods=["POST"])
#test http://127.0.0.1:4242/api/infos/
#test https://server.f80lab.com:4242/api/infos/
def save_config(name:str):
  if request.json is None:
    rc=request.data
  else:
    rc=dump(request.json,encoding="utf8")

  filename="./Configs/"+name+".yaml"
  f=open(filename,"w")
  f.writelines(str(rc,"utf8"))
  f.close()
  return jsonify({"error":""})




@app.route('/api/configs/<name>/')
@app.route('/api/configs/')
#test http://127.0.0.1:4242/api/infos/
#test https://server.f80lab.com:4242/api/infos/
def configs(name:str=""):
  if len(name)==0:
    return jsonify({"files":os.listdir("./Configs")})
  else:
    format=request.args.get("format","json")
    filename="./Configs/"+name+".yaml"
    if format=="json":
      f=open(filename,"r")
      s="\n".join(f.readlines())
      rc=load(s.replace("\n\n","\n"))
      f.close()
      return jsonify(rc)
    else:
      return send_file(path_or_file=filename,mimetype="plain/text",as_attachment=True,download_name=name+".yaml")








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
#https://metaboss.rs/set.html
#test http://127.0.0.1:9999/api/keys/
#test https://server.f80lab.com:4242/api/keys/
def keys():
  network=request.args.get("network","devnet").lower()
  if request.method=="GET":
    if "elrond" in network:
      return jsonify(Elrond(network).get_keys())
    else:
      return jsonify(Solana().get_keys())
  else:
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


@app.route('/api/explorer/',methods=["GET"])
@app.route('/api/scan/',methods=["GET"])
#https://metaboss.rs/mint.html
def explorer():
  token=request.args.get("token","")
  network=request.args.get("network","devnet")
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
  network=request.args.get("network","devnet")
  owner=request.args.get("owner")
  account=request.args.get("account","")
  rc=Solana(network).exec("use utilize",param="-h "+owner,account=account,keyfile=keyfile)
  return jsonify(rc)


@app.route('/api/sign/',methods=["GET"])
#https://metaboss.rs/mint.html
def sign():
  creator=request.args.get("creator","")
  keyfile=request.args.get("keyfile","paul")
  network=request.args.get("network","devnet")
  account=request.args.get("account","")
  log("Demande de signature pour "+keyfile)
  rc={}
  if len(account)>0:
    rc=Solana(network).exec("sign one",account=account,keyfile=keyfile)
  return jsonify(rc)



def upload_on_platform(data,platform="ipfs"):
  if platform=="ipfs":
    ipfs=IPFS("/ip4/161.97.75.165/tcp/5001/http",5001)
    cid=ipfs.add(data,removeFile=True)
    rc={"cid":cid["Hash"],"url":ipfs.get_link(cid["Hash"])+("?"+cid["Name"] if "Name" in cid else "")}

  if platform=="infura":
    infura=Infura()
    cid=infura.add(data)
    rc={"cid":cid,"url":ipfs.get_link(cid)}

  if platform=="nftstorage":
    if "content" in data:
      rc=NFTStorage().add(data["content"],data["type"],data["filename"])
    else:
      rc=NFTStorage().add(data)

  # if platform=="github":
  #   github_client=GitHubStorage(GITHUB)
  #

  return rc


#https://server.f80lab.com:4242/api/nfts/
@app.route('/api/nfts/',methods=["GET"])
def nfts():
  network=request.args.get("network","devnet")
  account=request.args.get("account","paul").lower()
  limit=request.args.get("limit","30")
  rc=[]
  if "elrond" in network:
    rc=rc+Elrond(network).get_nfts(account,IPFS(IPFS_SERVER,IPFS_PORT),int(limit))
  else:
    rc=rc+Solana(network).get_nfts(account)
  return jsonify(rc)

@app.route('/api/upload/',methods=["POST"])
#https://metaboss.rs/mint.html
def upload():
  platform=request.args.get("platform","ipfs")
  body={
    "filename":request.args.get("filename","temp"),
    "content":";base64,"+str(request.data,"utf8"),
    "type":request.args.get("type","")
  }

  if body["type"]=="":
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
  network=request.args.get("network","devnet")
  _data=request.json
  if _data is None:
    text=str(request.data,"utf8").replace('\x00','')
    _data=json.loads(text)

  if _data is None:
    s=str(request.data,"utf8")
    for i in range(200): s=s.replace("\r\n","")
    _data=json.loads(s)

  log("Minage avec les metadata "+str(_data))

  if "elrond" in network:
    elrond=Elrond(network)
    wallet_name=request.args.get("keyfile","paul").lower()

    collection_id=""
    for col in elrond.get_collections(wallet_name):
      if col["name"]==_data["collection"]["name"]:
        collection_id=str_to_hex(col["collection"],False)
        break

    if collection_id=="":
      collection_id=elrond.add_collection(wallet_name,_data["collection"]["name"],type="NonFungible")

    if collection_id:
      offchain={
        "attributes":_data["attributes"],
        "description":_data["description"],
        "collection":_data["collection"]["name"],
        "creators":_data["properties"]["creators"]
      }

      nonce=elrond.mint(wallet_name,
                     title=_data["name"],
                     collection=collection_id,
                     properties=offchain,
                     ipfs=IPFS(IPFS_SERVER,IPFS_PORT),
                     quantity=1,
                     royalties=20,
                     visual=_data["image"]
                     )
      if nonce is None:
        rc={"error":"Probleme de création"}
      else:
        infos=elrond.get_account(wallet_name)
        token_id=hex_to_str(collection_id)+"-"+nonce
        rc={"command":"ESDTCreate",
            "error":"",
            "link":elrond.getExplorer(token_id,"nfts"),
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
    else:
      log("Impossible de créé la collection du NFT")
      rc={"error":"Impossible de créé le NFT"}

  else:
    #****************************************************SOLANA
    if not "category" in _data["properties"]:
      _data["properties"]["category"]="image"

    offchain:dict={
      "attributes":_data["attributes"],
      "properties":_data["properties"],
      "description":_data["description"],
      "name":_data["name"],
      "image":_data["image"],
      "symbol":_data["symbol"]
    }

    offchain["external_url"]="" if not "exernal_url" in _data else _data["external_url"]

    upload_metadata=upload_on_platform(offchain,"ipfs")
    _data["uri"]=upload_metadata["url"]

    if "properties" in _data: _data["creators"]=_data["properties"]["creators"]

    for c in _data["creators"]:
      if len(c["address"])<20: c["address"]=Solana().find_address_from_json(c["address"])
      c["verified"]=False

    for k in ["properties","collection","image","attributes"]:
      if k in _data:del _data[k]

    rc=Solana(network).exec("mint one",keyfile=keyfile,data=_data,sign=(request.args.get("sign","False")=="True"),owner=request.args.get("owner",""))
    rc["balance"]=Solana(network).balance(keyfile)
    rc["unity"]="SOL"

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
  network=request.args.get("network","devnet")

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
    "UPDLOAD_FOLDER":"./Temp/"
  })




