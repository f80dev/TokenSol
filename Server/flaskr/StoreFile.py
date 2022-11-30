from os.path import exists

import yaml

from flaskr.settings import TEMP_DIR
from flaskr.NFT import NFT
from flaskr.Tools import now


class StoreFile:
  storefile_location=""
  content={"version":"1.0","nfts":[]}

  def __init__(self,storefile_location=TEMP_DIR+"storefile.yaml"):
    self.storefile_location=storefile_location
    if not exists(self.storefile_location):
      self.export_to_yaml()
    else:
      self.read_from_yaml()

  def export_to_yaml(self):
    with open(self.storefile_location,"w",encoding="utf-8") as f:
      yaml.dump(self.content,f)

  def read_from_yaml(self):
    self.content=yaml.safe_load(open(self.storefile_location,"r",encoding="utf-8").read())

  def lazymint(self,nft:NFT):
    if nft.address=="": nft.address="file_"+now("hex")
    self.content["nfts"].append(nft.__dict__)
    rc={
      "error":"",
      "tx":"",
      "result":{"transaction":"","mint":"file_"+nft.address},
      "balance":0,
      "link_mint":"",
      "link_transaction":"",
      "out": nft.toYAML(),
      "command":"insert"
    }
    return rc


