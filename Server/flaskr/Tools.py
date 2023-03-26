import base64
import csv
import datetime as datetime
import hashlib
import io
import json
import os
import random
import smtplib
from email import encoders
from email.mime.base import MIMEBase
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from io import BytesIO
from os.path import exists
from xml.dom import minidom

import PIL
import base58
import flask
import imageio
import numpy
import numpy as np
import pyqrcode
import requests
import unicodedata
import xml
import yaml

from PIL import Image,ImageSequence
from cryptography.fernet import Fernet
from fontTools import ttLib
from pandas import read_excel

from flaskr.secret import USERNAME, PASSWORD, SALT, UNSPLASH_SETTINGS, PIXABAY_SETTINGS
from flaskr.settings import SMTP_SERVER, SIGNATURE, APPNAME, SMTP_SERVER_PORT, OPERATIONS_DIR, STATIC_RESSOURCES_DIR


def get_hash_from_content(content):
  if type(content)==dict:
    content=json.dumps(content)

  if type(content)==str:
    if "<svg" in content: ext="svg"
    content=bytes(content,"utf8")

  return hashlib.sha256(content).hexdigest()




def get_filename_from_content(content,prefix_name="",ext="webp") -> str:
  if "/" in ext: ext=ext.split("/")[1].split("+")[0]

  hash=get_hash_from_content(content)

  return prefix_name+"_"+hash+"."+ext


def save_svg(svg_code,dir,dictionnary,prefix_name="svg") -> (str,str):
  """
  enregistrement d'un fichier svg après remplacement des mots clé contenu dans le fichier suivant le dictionnaire
  :param svg_code:
  :param dir:
  :param dictionnary:
  :param prefix_name:
  :return:
  """
  svg_code="<svg"+svg_code.split("<svg")[1]
  if dictionnary!={}:
    for k in dictionnary.keys():
      svg_code=svg_code.replace("_"+k+"_",str(dictionnary[k]))
      svg_code=svg_code.replace("__"+k+"__",str(dictionnary[k]))

  filename=get_filename_from_content(svg_code,prefix_name,ext="svg")
  with open(dir+filename,"w",encoding="utf8") as file:
    file.writelines(svg_code)
  file.close()

  return filename,svg_code

from itertools import product
def generate_svg_from_fields(svg_code) -> list:
  """
  génére plusieurs SVG en fonction des champs contenu dans le SVG si ces derniers contiennent des listes (format element_1|element_2|...|element_n)
  TODO: a améliorer pour croiser plusieurs listes
  :param svg_code:
  :return:
  """
  rc=[]

  #voir https://docs.python.org/fr/3/library/xml.dom.html#dom-element-objects
  doc:xml.dom.Document=minidom.parseString(svg_code)

  master_list=list()
  elts=doc.getElementsByTagName("desc")+doc.getElementsByTagName("title")
  for elt in elts:
    if len(elt.childNodes)>0:
      content=elt.childNodes[0].data
      if content and "|" in content:
        id=elt.parentNode.getElementsByTagName("tspan")[0].attributes["id"].nodeValue
        l=[{"id":id,"value":x} for x in content.split("|")]
        master_list.append(l)

  for tuples in product(*master_list):
    new_code=svg_code
    for val in tuples:
      for elt in doc.getElementsByTagName("tspan"):
        if elt.attributes["id"].nodeValue==val["id"]:
          new_code=new_code.replace(elt.firstChild.nodeValue+"</tspan>",val["value"]+"</tspan>")

    rc.append(minidom.parseString(new_code).toxml())

  if len(rc)==0: rc.append(svg_code)

  # if not bCreateFromMaster:
  #   rc.append(domain_server+"/api/images/"+file)

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
    #     rc.append(current_app.config["DOMAIN_SERVER"]+"/api/images/"+file)
    # else:
    #   rc.append(current_app.config["DOMAIN_SERVER"]+"/api/images/"+master.image)
  return rc


def get_fonts(dir="./Fonts/"):
  rc=[]
  for f in os.listdir(dir):
    try:
      tt = ttLib.TTFont(dir+f)
      info=tt.get("name")
      for name in info.names[:20]:
        if not "copyright" in str(name).lower() and not "©" in str(name) and len(str(name))<20:
          obj={"name":str(name),"file":f}
          if not obj["name"] in [x["name"] for x in rc]:
            rc.append(obj)
            break
          else:
            break
    except:
      log("Traitement du fichier "+f+" problématique")

  return rc


def is_email(addr):
  if addr is None:return False
  if len(addr)==0 or not "@" in addr:return False
  return True


def setParams(_d:dict,prefix="p="):
  rc=[]
  for k in _d.keys():
    value=_d[k]
    if type(value)==bool: value=str(value).lower() #<= compatibilité avec javascript
    if type(value)==dict: value=str(base64.b64encode(bytes(json.dump(value),"utf8")),"utf8")

    rc.append(k+"="+value)
  return prefix+str(base64.b64encode(bytes("&".join(rc),"utf8")),"utf8")




def send(app,event_name: str, message=None):
  try:
    if type(app)==flask.config.Config:
      socketio=app["socket"]
    else:
      socketio=app.config["socket"]
  except:
    log("WebSocket non disponible")
    return False

  if message:
    log("WebSocket.send "+str(message)+" a "+event_name)
    rc = socketio.emit(event_name,message)
  else:
    log("WebSocket.send de " + event_name)
    rc = socketio.emit(event_name)
  return rc

def returnError(msg:str="",_d=dict(),status=500):
  if type(msg)==RuntimeError: msg=str(msg.args[0])
  msg=str(msg)
  log("Error "+msg)
  if msg.startswith("!"): raise RuntimeError(msg[1:])
  return "Ooops ! Petit problème technique. "+msg,status


def random_from(elements="ABCDEFGHIJKLOMNOPQRST",n_elements=1):
  rc = []
  if len(elements)>0:
    while len(rc) < n_elements:
      rc.append(elements[random.randint(0, len(elements) - 1)])

  if n_elements==1:
    if len(rc)==0:
      return None
    else:
      return rc[0]
  else:
    return rc


def get_key_by_name(keys:[],name:str):
  for k in keys:
    if k.name==name: return k
  return None


def open_html_file(name:str,replace=dict(),domain_appli="",directory=STATIC_RESSOURCES_DIR):
  """
  ouvre un fichier html et remplace le code avec le dictionnaire de remplacement
  :param name:
  :param replace:
  :param domain_appli:
  :return:
  """
  if name.startswith("http"):
    body=requests.get(name).text
  else:
    if name is None: return None
    if len(name)>10 and len(name.split(" "))>5:
      body=name
    else:
      if not name.endswith("html"):name=name+".html"
      if exists(directory+name):
        with open(directory+name, 'r', encoding='utf-8') as f: body = f.read()
      else:
        log("Le mail type "+name+" n'existe pas")
        return None

  style="""
        <style>
        .button {
         border: none;
         background: #d9d9d9;
         color: #fff;
         padding: 10px;
         display: inline-block;
         margin: 10px 0px;
         font-family: Helvetica, Arial, sans-serif;
         font-weight: lighter;
         font-size: large;
         -webkit-border-radius: 3px;
         -moz-border-radius: 3px;
         border-radius: 3px;
         text-decoration: none;
        }

     .button:hover {
        color: #fff;
        background: #666;
     }
    </style>
    """

  replace["signature"]=SIGNATURE
  replace["appname"]=APPNAME
  replace["appdomain"]=domain_appli

  for k in list(replace.keys()):
    body=body.replace("{{"+k+"}}",str(replace.get(k)))

  body=body.replace("</head>",style+"</head>")

  return body


def is_encrypt(content:str):
  s=decrypt(bytes(content,"utf8"))
  if s==content: return True
  return False

def decrypt(content:bytes,secret_key_filename="./secret_key") -> str:
  """
  fonction de decryptage
  :param text:
  :return:
  """
  if type(content)==str:content=base64.b64decode(bytes(content,"utf8"))

  try:
    with open(secret_key_filename,"rb") as file:
      key=file.read(10000)
    f=Fernet(key)
    return str(f.decrypt(content),"utf8")
  except:
    return content



def convert_to_ascii(s:str):
  s=s.upper()
  return "".join([char for char in s if char.isalpha()])

def simplify_email(email):
  email_encoded=convert_to_ascii(email)
  email_encoded=email_encoded[:len(email_encoded)-6] #On enleve la fin de l'email que l'on considère comme non utile
  return email_encoded

def encrypt(text:str,secret_key_filename="./secret_key",format="str",short_code=0):
  """
  fonction d'encryptage utilisant le fichier secret_key du repertoire principale
  :param text:
  :return:
  """
  if short_code>0:
    encoder=hashlib.blake2s(digest_size=int(short_code/2))
    encoder.update(bytes(text,"utf8"))
    rc=encoder.hexdigest()
    return rc

  if exists(secret_key_filename):
    with open(secret_key_filename,"rb") as file:
      key=file.read()
  else:
    key = Fernet.generate_key()
    with open(secret_key_filename,"wb") as file:
      file.write(key)

  f=Fernet(key)
  rc=f.encrypt(text.encode())
  if format=="str" or format=="txt":return str(base64.b64encode(rc),"utf8")
  return rc


def send_mail(body:str,_to="paul.dudule@gmail.com",_from:str="contact@nfluent.io",subject="",attach=None,filename=""):
  if body is None or not is_email(_to):return False
  with smtplib.SMTP(SMTP_SERVER, SMTP_SERVER_PORT,timeout=10) as server:
    server.ehlo()
    server.starttls()
    try:
      log("Tentative de connexion au serveur de messagerie")
      server.login(USERNAME, PASSWORD)
      log("Connexion réussie. Tentative d'envoi")

      msg = MIMEMultipart()
      msg.set_charset("utf-8")
      msg['From'] = _from
      msg['To'] = _to
      msg['Subject'] = subject
      msg.attach(MIMEText(body,"html"))

      if not attach is None:
        part = MIMEBase('application', "octet-stream")
        part.set_payload(attach)
        encoders.encode_base64(part)
        part.add_header('Content-Disposition',"attachment",filename=filename)
        msg.attach(part)

      log("Send to "+_to+" <br><div style='font-size:x-small;max-height:300px>"+body+"</div>'")
      server.sendmail(msg=msg.as_string(), from_addr=_from, to_addrs=[_to])
      return True
    except Exception as inst:
      log("Echec de fonctionement du mail"+str(type(inst))+str(inst.args))
      return False


def str_to_int(letters):
  return int(str_to_hex(letters),16)

def int_to_hex(number,nbChar=2,zerox=True):
  rc=hex(int(number))
  if zerox:rc=rc.replace("0x","")
  if len(rc)<nbChar:
    rc="0"*(nbChar-len(rc))+rc
  return rc


def filetype(filename=""):
  if filename.endswith(".jpg") or filename.endswith(".psd") or filename.endswith(".png") or filename.startswith("data:image") or filename.endswith("webp"):return "image"
  if filename.endswith(".json"):return "json"
  if filename.endswith(".txt"):return "text"
  return filename[filename.rindex(".")+1:]

def api(url,alternate_domain="",timeout=60000):
  log("Appel de "+url)
  data=requests.api.get(url)

  if data.status_code!=200:
    if len(alternate_domain)>0:
      url=url.replace(alternate_domain.split("=")[0],alternate_domain.split("=")[1])
      log("Appel de "+url)

    data=requests.api.get(url,timeout=timeout)

    if data.status_code!=200:
      log("Echec de l'appel "+str(data.status_code)+" "+data.text)
      return None

  try:
    return data.json()
  except:
    return data.text



def get_qrcode(text:str,scale=3):
  buffer=BytesIO()
  pyqrcode.create(text).png(buffer,scale=scale)
  return "data:image/png;base64,"+str(base64.b64encode(buffer.getvalue()),"utf8")



def hex_to_str(number):
  number=''.join([x for x in number if ord(x)>=ord('0')])
  if not type(number)==str:
    number=hex(number)[2:]
  rc=""
  for i in range(0,len(number),2):
    rc=rc+chr(int(number[i:i+2],16))
  return rc


#
# def int_to_hex(number,digits=2,zerox=False):
#   s=hex(number)
#   if not zerox:s=s.replace("0x","")
#   while len(s)<digits: s="0"+s
#   return s



def str_to_hex(letters,zerox=True):
  if type(letters)==int:
    rc=hex(letters).replace("0x","")
  else:
    if type(letters)==list:letters=",".join(letters)
    rc=""
    for letter in letters:
      rc=rc+hex(ord(letter))[2:]

  if len(rc) % 2==1:rc="0"+rc
  rc=rc.lower()

  if zerox:
    return "0x"+rc
  else:
    return rc


def get_operation(name:str,with_comment=False):
  if name is None: return None
  if type(name)==str:
    if len(name)==0: return None
    if name.startswith("b64:") or name.startswith("http"):
      url=name
      if name.startswith("b64:"): url=str(base64.b64decode(name[4:]),"utf8")
      text=requests.get(url).text
      rc=yaml.load(text,Loader=yaml.FullLoader)
      rc["id"]=name if name.startswith("b64:") else "b64:"+str(base64.b64encode(bytes(name,"utf8")),"utf8")
    else:
      name=name.replace(".yaml","")
      text=open(OPERATIONS_DIR+name+".yaml","r").read()
      rc=yaml.load(text,Loader=yaml.FullLoader)

  #Complément pour les parties manquantes
  if not "transfer" in rc:rc["transfer"]={"mail":""}
  if not "new_account" in rc:rc["new_account"]={"mail":""}

  #Complement des operations
  if "validate" in rc:
    if not "collections" in rc["validate"]["filters"] or len(rc["validate"]["filters"]["collections"])==0:
      if "lazy_mining" in rc and len(rc["lazy_mining"]["networks"])>0 and "collection" in rc["lazy_mining"]["networks"][0]:
        rc["validate"]["filters"]["collections"]=[rc["lazy_mining"]["networks"][0]["collection"]]
      else:
        rc["validate"]["filters"]["collections"]=[]
        for src in rc["data"]["sources"]:
          if "collections" in src:
            rc["validate"]["filters"]["collections"].append(src["collections"])

    if "users" in rc["validate"]:
      rc["validate"]["access_codes"]=[]
      if rc["validate"]["users"]:
        for user in rc["validate"]["users"]:
          rc["validate"]["access_codes"].append(get_access_code_from_email(user))

  if with_comment: return rc,text
  return rc


def strip_accents(text):
  text = unicodedata.normalize('NFD', text) \
    .encode('ascii', 'ignore') \
    .decode("utf-8")

  return str(text)



def queryPixabay(query:str,limit:int=10,quality:bool=False,square=False):
  """
  Interrogation de pixabay pour obtenir les images demandées via query
  voir https://pixabay.com/api/docs/#api_search_images
  :param query: contient le mot clé à utiliser pour rechercher les images
  :param limit: nombre d'images retournées
  :param quality: permet de restreindre la recherche aux photos de l'éditeur
  :return: liste au format json des urls des photos correspondantes à la requête
  """
  if limit==0: return []
  params=("&colors=transparent" if "sticker" in query else "")
  if len(query.split(" "))>1: query=query.replace("sticker","").replace("transparent","")

  url=PIXABAY_SETTINGS["endpoint"]+"?per_page="+str(limit)+"&key=" + PIXABAY_SETTINGS["key"] + params + "&q=" + query
  if quality:url=url+"&editors_choice=true"

  rc=[]
  for image in requests.get(url).json()["hits"]:
    rc.append(image["largeImageURL"])

  return rc


def isLocal(url:str):
  return "localhost" in url or "127.0.0.1" in url

def queryUnsplash(query,limit=10,square=False):
  """
  Interrogation de pixabay pour obtenir les images demandées via query
  voir https://unsplash.com/documentation#search-photos
  :param query:  contient le mot clé à utiliser pour rechercher les images
  :return: liste au format json des urls des photos correspondant à la requête
  """
  if limit==0: return []
  url = UNSPLASH_SETTINGS["endpoint"] \
        + "search/photos?query="+query+"&per_page=" \
        +str(limit)+"&client_id=" + UNSPLASH_SETTINGS["key"]+("&orientation=squarish" if square else "")

  rc=list()
  for image in requests.get(url).json()["results"]:
    rc.append(image["urls"]["raw"])

  return rc


#Retourne la date du jour en secondes
def now(format="dec"):
  rc= datetime.datetime.now(tz=None).timestamp()
  if format=="hex":return hex(int(rc*10000))
  if format=="random":return hex(int(rc*10000)+random.randint(0,1000000))
  return rc


def extract_from_dict(_d:dict,fields,default=None):
  """
  tag : readdict,getdict, get_dict
  :param _d:
  :param fields:
  :param default:
  :return:
  """
  if type(fields)==str:
    sep="," if not "\n" in fields else "\n"
    fields=fields.split(sep)

  for field in fields:
    if field in _d:return _d[field]
  log("Aucun champs "+" ".join(fields)+" dans "+str(_d))
  return default


start=now()
store_log=""
def log(text:str,sep='\n',raise_exception=False):
  global store_log
  if text.startswith("\n"):
    print("\n\n")
    text=text[1:]

  delay=int(now()-start)
  line:str=str(int(delay/60))+":"+str(delay % 60)+" : "+text
  try:
    print(line)
  except:
    print("Problème d'affichage d'une ligne")
  store_log = line+sep+store_log[0:10000]
  if raise_exception or text.startswith("!"):raise RuntimeError(text)
  return text


def get_timestamp_for_access_code():
  return int(datetime.datetime.now().timestamp()/60)

def get_access_code(addr:str) -> str:
  """
  fournis un qrcode temporaire pour la connexion via nfluent_wallet_connect
  :param addr:
  :return:
  """
  return encrypt(addr+"ts:"+str(get_timestamp_for_access_code()))


def get_access_code_from_email(email:str):
  """
  fournis le mot de passe pour les validateurs sur la base de leur mail
  seul les 6 premiers caractères sont transmis
  :param email:
  :return:
  """
  return hashlib.md5((email+SALT).encode()).hexdigest().upper()[:8]


def normalize(s:str) -> str:
  return s.lower().replace(" ","")


def check_access_code(code:str) -> str:
  """
  Vérification d'un code d'accès obtenu sur base d'un email
  :param code: 
  :return: 
  """""
  try:
    s=decrypt(bytes(code,"utf8"))
  except:
    log("Code incorrect")
    return ""

  ts=int(s.split("ts:")[1])
  #On vérifie la resence du timestamp
  if ts!=get_timestamp_for_access_code(): return None
  return s.split("ts:")[0]



def convertImageFormat(imgObj, outputFormat=None):
  """
  Convertion vers le outputFormat
  Pour l'instant ne fonctionne qu'avec le GIF
  :param imgObj:
  :param outputFormat:
  :return:
  """
  newImgObj = imgObj

  if outputFormat:
    outputFormat=outputFormat.upper()
    if (imgObj.format != outputFormat):
      imageBytesIO = BytesIO()
      imgObj.save(imageBytesIO, outputFormat,save_all=True,optimize=True,quality=95)
      newImgObj = Image.open(imageBytesIO)

  return newImgObj


def extract_image_from_string(content:str) -> Image:
  if type(content)==bytes:
    rc=Image.open(io.BytesIO(content),formats=["GIF"])
    return rc

  if "base64" in content:
    content=content.split("base64,")[1]
    content=base64.b64decode(content)

  if "<svg" in str(content):
    return str(content,"utf8")      #On est en présence d'un SVG

  return Image.open(io.BytesIO(content))



def convert_to(content:str,storage_platform=None,filename=None,format="GIF",quality=90):
  if content.startswith("http"):
    image:Image=Image.open(io.BytesIO(requests.get(content).content))
  else:
    image:Image=extract_image_from_string(content)

  if filename:
    buffered=open(filename,"wb")
  else:
    buffered =io.BytesIO()

  if image.format!="JPEG" and image.is_animated:
    frames = [f.convert("RGBA") for f in ImageSequence.Iterator(image)]
    frames[0].save(buffered,format=format,save_all=True,append_images=frames[1:],optimize=True,quality=quality)
  else:
    image.save(buffered, format=format,quality=quality)

  if storage_platform:
    url=storage_platform.add(bytes(buffered.getvalue()),"image/gif")["url"]
    return url

  if filename:
    buffered.close()
    return filename

  return buffered



def convert_image_to_animated(base:Image,n_frames:int,prefix_for_temp_file="temp_convert",format_to_use="gif",temp_dir="./temp/"):
  """
  Converti une image fixe en image animée
  voir https://pillow.readthedocs.io/en/stable/handbook/tutorial.html#image-sequences
  :param base:
  :param n_frames:
  :param prefix_for_temp_file:
  :param format_to_use:
  :param temp_dir:
  :return:
  """

  filename=temp_dir+prefix_for_temp_file+"_"+now("hex")+"."+format_to_use
  #log("Convertion de "+str(base)+" en image animé de "+str(n_frames)+" frames -> "+filename)

  #base=convertImageFormat(base,format_to_use).copy()
  base=base.convert("RGB")
  base=Image.new("RGB",(100,100),(100,100,100))

  filenames=[]
  for i in range(n_frames):
    filename_seq=temp_dir+"_iter"+str(i)+"."+format_to_use
    base.save(filename_seq)
    filenames.append(filename_seq)

  images=[Image.open(file_name) for file_name in filenames]

  # random_pixels = np.random.rand(100, 100, 3) * 255
  # images = [Image.fromarray(random_pixels.astype("uint8")) for i in range(10)]

  #images=[base]*(n_frames)

  #voir https://pillow.readthedocs.io/en/stable/handbook/image-file-formats.html
  gif=images[0]
  gif.save(filename, format=format_to_use,save_all=True, append_images=images[1:])

  #Fermeture des images
  base.close()
  for image in images: image.close()

  rc= Image.open(filename,mode="r",formats=[format_to_use])
  return rc


def transfer_sequence_to_disk(img:Image,dir="./temp/"):
  i=0
  for f in ImageSequence.Iterator(img):
    i=i+1
    f.save(dir+img.name+"_seq_"+str(i)+".gif")
  return True


def merge_animated_image(base:Image,to_paste:Image,prefix_for_temp_file="temp_merge",temp_dir="./temp"):
  filename=temp_dir+prefix_for_temp_file+"_"+now("hex")+".gif"
  wr=imageio.get_writer(filename,mode="I")

  frames_to_paste = [f.resize(base.size).convert("RGBA").copy() for f in ImageSequence.Iterator(to_paste)]
  frame_base=[f.convert("RGBA").copy() for f in ImageSequence.Iterator(base)]

  #Equilibre le nombre d'image de chaque sur la base et le a coller
  n_frame_base=len(frame_base)
  n_frame_to_paste=len(frames_to_paste)
  for i in range(abs(n_frame_to_paste-n_frame_base)):
    if n_frame_to_paste>n_frame_base:
      frame_base.append(frame_base[n_frame_base-1].copy())
    else:
      frames_to_paste.append(frames_to_paste[n_frame_to_paste-1].copy())

  for i in range(max(n_frame_base,n_frame_to_paste)):
    frame_base[i].alpha_composite(frames_to_paste[i])

    ndarray=numpy.asarray(frame_base[i])
    wr.append_data(ndarray)

  wr.close()
  to_paste.close()
  rc=Image.open(filename,"r")
  return rc




def idx(col:str,row=None,default=None,max_len=100,min_len=0,replace_dict:dict={},header=list()):
  """
  Permet l'importation dynamique des colonnes
  version 1.0
  :param col:
  :param row:
  :param default:
  :param max_len:
  :param min_len:
  :param replace_dict:
  :param header:
  :return:
  """
  for c in col.lower().split(","):
    if c in header:
      if row is not None and len(row)>header.index(c):
        rc=str(row[header.index(c)])

        #Application des remplacement
        for old in replace_dict.keys():
          rc=rc.replace(old,replace_dict[old])

        if max_len>0 and len(rc)>max_len:rc=rc[:max_len]
        if min_len==0 or len(rc)>=min_len:
          return rc.strip()
      else:
        return header.index(c)
  return default


def importer_file(file):
  """
  Systeme d'importation de fichier csv ou excel
  version 1.0
  :param file:
  :return:
  """
  d=list()

  log("Importation de fichier")
  data=file
  if type(file)==str:
    if len(file)>500:
      if "base64," in file: file=str(file).split("base64,")[1]
      data = base64.b64decode(file)
    else:
      #test http://localhost:4200/mint?import=https:%2F%2Fgithub.com%2Ff80dev%2FTokenSol%2Fblob%2Fmaster%2FServer%2Ftests%2Fressources%2Fbatch_importation.xlsx%3Fraw%3Dtrue
      if file.startswith("http"):
        data=requests.get(file).content

  res=None
  if type(data)==bytes:
    res = read_excel(data)
  else:
    if data.endswith("xlsx"):
      res = read_excel(data)
    else:
      delimiter = ";"
      text_delimiter = False
      log("Analyse du document")
      for _encoding in ["utf-8", "ansi"]:
        try:
          txt = str(data, encoding=_encoding)
          break
        except:
          pass
      txt = txt.replace("&#8217;", "")
      log("Méthode d'encoding " + _encoding)

      if "\",\"" in txt:
        delimiter = ","
        text_delimiter = True

        log("Importation du CSV")
        res = csv.reader(io.StringIO(txt), delimiter=delimiter, doublequote=text_delimiter)

  if res is None:
    return None,0
  else:
    d.append(list(res))
    for k in range(1, len(res)):
      d.append(list(res.loc[k]))
    total_record = len(d) - 1
    log("Nombre d'enregistrements identifié " + str(total_record))

  return d,total_record





