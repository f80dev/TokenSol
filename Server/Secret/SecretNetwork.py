from secret_sdk.client.lcd import LCDClient

#documentation
#faucet : https://faucet.secrettestnet.io/
from secret_sdk.key.key import Key


class SecretNetwork:
  def __init__(self,chain_id="pulsar-2",node_rest_endpoint="https://secret-pulsar-2--lcd--full.datahub.figment.io"):
    self.api = LCDClient(chain_id=chain_id,url=node_rest_endpoint)

  def balance(self,addr):
    return self.api.wallet(Key(addr)).account_number()

  def infos(self):
    return self.api.tendermint.block_info()["block"]

  def mint(self):
    """
    voir https://learn.figment.io/tutorials/create-your-first-secret-nft
    voir le standard SNIP721 : https://github.com/SecretFoundation/SNIPs/blob/master/SNIP-721.md
    documentation secret python : https://github.com/secretanalytics/secret-sdk-python

    :return:
    """

    pass
    # wallet = wallet(mk)
