import base64
import json
import os
from datetime import datetime
from io import FileIO

import requests
from ipfshttpclient import Client
from multiaddr import Multiaddr


class IPFS:
    client=None

    def __init__(self, addr:str,port:int):
        self.client=Client(Multiaddr(addr))


    def add_file(self, file):
        cid=self.client.add(file)
        return cid["Hash"]


    def get(self,token):
        file=self.client.get(token)
        return file


    def add(self,body,removeFile=False,temp_dir="./Solana/Temp/"):
        f=None
        if type(body)==dict:
          if "filename" in body:
            f=open(temp_dir+body["filename"],"wb")
            f.write(base64.b64decode(body["content"].split(";base64,")[1]))
            f.close()

            cid=self.client.add(temp_dir+body["filename"])
          else:
            cid={"Hash":self.client.add_json(body)}

        if type(body)==bytes:
          cid={"Hash":self.client.add_bytes(body)}

        if type(body)==str:
          cid={"Hash":self.client.add_str(body)}

        if removeFile and f: del f
        cid["url"]="https://ipfs.io/ipfs/"+cid["Hash"]

        return cid



    def get_dict(self,token):
        if len(token)!=46: return token
        url="https://ipfs.io/ipfs/"+token
        r=requests.get(url)
        try:
            return json.loads(r.text.replace("'","\""))
        except:
            return r

    def get_link(self, cid):
        return "https://ipfs.io/ipfs/"+cid
