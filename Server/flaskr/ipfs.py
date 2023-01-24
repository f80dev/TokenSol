import base64
import json
import requests
from ipfshttpclient import Client
from multiaddr import Multiaddr

from flaskr.Storage import Storage

"""
voir https://docs.ipfs.tech/how-to/run-ipfs-inside-docker/
Gestion d'une instance IPFS sur le serveur
mkdir /root/ipfs
mkdir /root/ipfs/staging
mkdir /root/ipfs/data
firewall-cmd --zone=public --add-port=5001/tcp
firewall-cmd --zone=public --add-port=4001/tcp
firewall-cmd --zone=public --add-port=8080/tcp

firewall-cmd --zone=trusted --remove-interface=docker0 --permanent
firewall-cmd --reload

export ipfs_staging=/root/ipfs/staging
export ipfs_data=/root/ipfs/data

docker pull ipfs/kubo
docker rm -f ipfs_host
docker run -d --restart=always --name ipfs_host -v $ipfs_staging:/export -v $ipfs_data:/data/ipfs -p 4001:4001/udp -p 8080:8080 -p 5001:5001 ipfs/kubo:latest

A priori inutile:



"""
class IPFS(Storage):

    client=None

    def __init__(self, addr:str):
        self.client=Client(Multiaddr(addr))


    def add_file(self, file:str):
        cid=self.client.add(file)
        rc=dict(cid)
        rc["filename"]=rc["Name"]
        rc["url"]="https://ipfs.io/ipfs/"+rc["Hash"]
        return rc


    def get(self,token):
        file=self.client.get(token)
        return file


    def add(self,body,removeFile=False,temp_dir="./Solana/Temp/"):
        f=None
        if type(body)==dict or type(body)==list:
          if "content" in body:
            body=base64.b64decode(body["content"].split(";base64,")[1])
          else:
            cid={"Hash":self.client.add_json(body)}

        if type(body)==bytes:
          cid={"Hash":self.client.add_bytes(body)}

        if type(body)==str:
          cid={"Hash":self.client.add_str(body)}

        if removeFile and f: del f
        cid["url"]="https://ipfs.io/ipfs/"+cid["Hash"]
        if type(body)==dict and "filename" in body: cid["filename"]=body["filename"]

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
