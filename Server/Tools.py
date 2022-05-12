import datetime as datetime

import requests


def str_to_int(letters):
  return int(str_to_hex(letters),16)

def int_to_hex(number,nbChar=2,zerox=True):
  rc=hex(int(number))
  if zerox:rc=rc.replace("0x","")
  if len(rc)<nbChar:
    rc="0"*(nbChar-len(rc))+rc
  return rc


def filetype(filename=""):
  if filename.endswith(".jpg") or filename.endswith(".png") or filename.startswith("data:image"):return "image"
  if filename.endswith(".json"):return "json"
  if filename.endswith(".txt"):return "text"
  return filename[filename.rindex(".")+1:]

def api(url,alternate_domain=""):
  log("Appel de "+url)
  data=requests.api.get(url)

  if data.status_code!=200:
    log("Appel de "+url)
    if len(alternate_domain)>0:
      url=url.replace(alternate_domain.split("=")[0],alternate_domain.split("=")[1])

    data=requests.api.get(url)

    if data.status_code!=200:
      log("Echec de l'appel "+str(data.status_code)+" "+data.text)
      return None

  try:
    return data.json()
  except:
    return data.text




def hex_to_str(number):
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


#Retourne la date du jour en secondes
def now():
  rc= datetime.datetime.now(tz=None).timestamp()
  return rc


start=now()
store_log=""
def log(text:str,sep='\n'):
  global store_log
  delay=int(now()-start)
  line:str=str(int(delay/60))+":"+str(delay % 60)+" : "+text
  print(line)
  store_log = line+sep+store_log[0:10000]
  return text
