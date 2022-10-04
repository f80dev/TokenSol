import base64
import datetime as datetime
import json
import os
import smtplib
from email import encoders
from email.mime.base import MIMEBase
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from io import BytesIO
from os.path import exists

import pyqrcode
import requests
import unicodedata
import yaml
from cryptography.fernet import Fernet
from fontTools import ttLib


from secret import USERNAME, PASSWORD
from settings import SMTP_SERVER, SIGNATURE, APPNAME, SMTP_SERVER_PORT


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


def setParams(_d:dict,prefix="param="):
  rc=[]
  for k in _d.keys():
    value=_d[k]
    if type(value)==bool: value=str(value).lower() #<= compatibilité avec javascript
    if type(value)==dict: value=str(base64.b64encode(bytes(json.dump(value),"utf8")),"utf8")

    rc.append(k+"="+value)
  return prefix+str(base64.b64encode(bytes("&".join(rc),"utf8")),"utf8")




def open_html_file(name:str,replace=dict(),domain_appli=""):
  if not name.endswith("html"):name=name+".html"
  with open("./"+name, 'r', encoding='utf-8') as f: body = f.read()

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



def decrypt(content:bytes,secret_key_filename="./secret_key") -> str:
  """
  fonction de decryptage
  :param text:
  :return:
  """
  if type(content)==str:content=base64.b64decode(content)

  with open(secret_key_filename,"rb") as file:
    key=file.read(10000)
  f=Fernet(key)
  return str(f.decrypt(content),"utf8")



def encrypt(text:str,secret_key_filename="./secret_key"):
  """
  fonction d'encryptage utilisant le fichier secret_key du repertoire principale
  :param text:
  :return:
  """
  if exists(secret_key_filename):
    with open(secret_key_filename,"rb") as file:
      key=file.read()
  else:
    key = Fernet.generate_key()
    with open(secret_key_filename,"wb") as file:
      file.write(key)

  f=Fernet(key)
  return f.encrypt(text.encode())


def send_mail(body:str,_to="paul.dudule@gmail.com",_from:str="contact@nfluent.io",subject="",attach=None,filename=""):
  if not is_email(_to):return None
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


def get_operation(name:str):
  if name.startswith("b64:"): name=str(base64.b64decode(name.split("b64:")[1]),"utf8")
  if name.startswith("http"):
    rc=requests.get(name).text
    rc=yaml.load(rc,Loader=yaml.FullLoader)
  else:
    name=name.replace(".yaml","")
    rc=yaml.load(open("./Operations/"+name+".yaml","r"),Loader=yaml.FullLoader)
  return rc


def strip_accents(text):
  text = unicodedata.normalize('NFD', text) \
    .encode('ascii', 'ignore') \
    .decode("utf-8")

  return str(text)


#Retourne la date du jour en secondes
def now(format="dec"):
  rc= datetime.datetime.now(tz=None).timestamp()
  if format=="hex":return hex(int(rc*10000))
  return rc


start=now()
store_log=""
def log(text:str,sep='\n'):
  global store_log
  delay=int(now()-start)
  line:str=str(int(delay/60))+":"+str(delay % 60)+" : "+text
  try:
    print(line)
  except:
    print("Problème d'affichage d'une ligne")
  store_log = line+sep+store_log[0:10000]
  return text


def get_timestamp_for_access_code():
  return int(datetime.datetime.now().timestamp()/60)

def get_access_code(addr:str) -> str:
  return encrypt(addr+"ts:"+str(get_timestamp_for_access_code()))

def check_access_code(code:str) -> str:
  s=decrypt(bytes(code,"utf8"))
  ts=int(s.split("ts:")[1])
  #On vérifie la resence du timestamp
  if ts!=get_timestamp_for_access_code(): return None
  return s.split("ts:")[0]
