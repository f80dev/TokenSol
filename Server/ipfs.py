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


    def add(self,body,removeFile=False):
        if type(body)==dict:
          if "filename" in body:
            f=open("./Temp/"+body["filename"],"wb")
            f.write(base64.b64decode(body["content"].split(";base64,")[1]))
            f.close()
            if removeFile:
              del f

            cid=self.client.add("./Temp/"+body["filename"])
          else:
            cid=self.client.add_json(body)

        if type(body)==bytes:
          cid=self.client.add_bytes(body)

        if type(body)==str:
          cid=self.client.add_str(body)

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
