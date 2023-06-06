import base64

from pathlib import Path

import requests
from multiversx_sdk_core import Transaction, Address, TransactionPayload, TokenPayment

from multiversx_sdk_network_providers.accounts import AccountOnNetwork

from multiversx_sdk_wallet import Mnemonic

from flaskr.Keys import Key
from flaskr.NFluentAccount import NfluentAccount
from flaskr.Network import Network
from flaskr.Storage import Storage
from bitcoinlib.wallets import Wallet

from flaskr.dao import DAO
import json

from os import listdir

from time import sleep
import pyqrcode
from flaskr.Tools import hex_to_str, now, get_access_code_from_email, int_to_hex, str_to_hex, log, api, \
  send_mail, open_html_file, strip_accents, returnError, decrypt, extract_title_from_html, get_hash, extract_from_dict
from flaskr.NFT import NFT
import textwrap

class Bitcoin(Network):

  def __init__(self,network="bitcoin-devnet"):
    super().__init__(network)



  def get_unity(self):
    return "btc"

  def toAddress(self,private_key:str):
    return private_key[0:16]


  def canMint(self,nft_to_check:NFT,dest:str="",miner:str=""):
    """
    Vérifie si un NFT a déjà été miné ou pas
    TODO: fonction à coder
    :param nft_to_check:
    :return:
    """
    return True



  def get_transactions_from_collection(self,address,size=300):
    pass



  def get_transactions(self,address,limit=1000,size=10,profondeur=0,profondeur_max=3,methods=[],exclude_addresses=[]):
    pass




  def getExplorer(self, tx="", _type="transactions") -> str:
    pass


  def getWallet(self,addr=""):
    pass



  def send_transaction(self, _sender: Key,
                       _receiver: AccountOnNetwork or Address or str,
                       _sign: Key,
                       data: str=None,
                       value=None,
                       transaction=None,
                       timeout=120, simulation=False, delay_between_check=1.0, ):
    """
    Envoi d'une transaction signée
    voir https://docs.multiversx.com/sdk-and-tools/sdk-py/sdk-py-cookbook#egld--esdt-transfers
    :param _sender:
    :param _receiver:
    :param _sign:
    :param value:
    :param data:
    :return:
    """
      return {"error":"","status":"error"}




  def get_collections(self, addr:str, detail:bool=True, type_collection="", special_role=""):
    """
    récupération des collections voir : https://devnet-api.multiversx.com/#/accounts/AccountController_getAccountCollectionsWithRoles
    :param creator:
    :param fields:
    :return:
    """

    pass



  def get_collection(self,collection_id):
    pass


  def transfer_money(self,nft_addr:str,miner:Key,to_addr:str,quantity=1,data=""):
    """
    voir https://docs.multiversx.com/sdk-and-tools/sdk-py/sdk-py-cookbook/#egld--esdt-transfers
    :param nft_addr:
    :param miner:
    :param to_addr:
    :param quantity:
    :return:
    """
    pass





  def transfer(self,nft_addr:str,miner:Key,to_addr:str,quantity=1):
    pass


  def get_balance(self,addr,token_id="") -> int:
    pass








  def add_collection(self, owner:Key, collection_name:str,options:list=[],type_collection="SemiFungible",simulation=False) -> (dict):
    pass


  def get_nfts_from_collections(self,collections:[str],with_attr=False,format="class"):
    """
    voir https://api.elrond.com/#/collections/CollectionController_getNftCollection
    :param collections:
    :param miner:
    :return:
    """
    pass



  def get_account(self,addr:str) -> NfluentAccount:
    pass

  def get_balances(self, addr:str,nft_addr=None) -> dict():
    pass



  def get_pem(self,secret_key: bytes, pubkey: bytes):
    pass



  def create_account(self,email="",seed="",domain_appli="",
                     subject="",
                     mail_new_wallet="",mail_existing_wallet="",
                     send_qrcode_with_mail=True,dictionnary={},
                     histo:DAO=None,send_real_email=True) -> Key:
    """
    voir
    :param fund:
    :param name:
    :param seed_phrase:
    :return: Account, PEM,words,qrcode
    """
    if histo:
      pubkey=histo.get_address(email,self.network)
      if pubkey:
        log("Impossible de créer un deuxième compte pour cette adresse "+pubkey)
        if send_real_email:
          url_explorer=self.getExplorer(pubkey,"accounts")
          if len(subject)==0: subject=extract_title_from_html(mail_existing_wallet,dictionnary)
          send_mail(open_html_file(mail_existing_wallet,{
            "wallet_address":pubkey,
            "blockchain_name":"MultiversX",
            "mini_wallet":self.nfluent_wallet_url(pubkey,domain_appli),
            "nfluent_wallet":self.nfluent_wallet_url(pubkey,domain_appli),
            "official_wallet":"https://xportal.com/",
            "url_explorer":url_explorer,
            "url_gallery":self.getGallery(pubkey),
          },domain_appli=domain_appli),email,subject=subject)
          return Key(address=pubkey,name=email.split("@")[0],network="elrond")

    log("Création d'un nouveau compte")
    qrcode=""
    if len(seed) == 0:
      mnemonic =Mnemonic.generate()
      words= mnemonic.get_words()


    wallet=Wallet.create(keys=words.split(" "))
    secret_key=wallet.

    log("Création du compte "+self.getExplorer(wallet,"address"))

    if len(email)>0:
      wallet_appli=self.nfluent_wallet_url(address,domain_appli)
      if not send_qrcode_with_mail:qrcode=None
      if send_real_email:
        url_explorer=self.getExplorer(address,"accounts")

        if send_mail(open_html_file(mail_new_wallet,{
          "wallet_address":address,
          "mini_wallet":wallet_appli,
          "url_wallet":self.getWallet(address),
          "url_explorer":url_explorer,
          "words":" ".join(words),
          "qrcode":"cid:qrcode",
          "access_code":get_access_code_from_email(address)
        },domain_appli=domain_appli),email,subject=subject):
          if histo: histo.add_email(email,address,self.network)

    return Key(secret_key.hex(),name=email.split("@")[0],address=address,seed=words)


  def analyse_attributes(self,body,with_ipfs=True,timeout=2) -> (list,str,str,list):
    """
    analyse du champs attributes des NFT elrond (qui peut contenir les données onchain ou via IPFS)
    :param body:
    :return: les attributs, description, les tags
    """
    tags=""
    desc=""
    creators=[]
    try:
      attr=str(base64.b64decode(bytes(body,"utf8")),"utf8")
    except:
      attr=str(base64.b64decode(body))

    #log("Pour les attributs, analyse de la chaine "+attr)

    if "tags:" in attr:
      tags=attr.split("tags:")[1].split(";")[0]

    if "metadata" in attr:
      cid=attr.split("metadata:")[1].split(";")[0]
      #log("Recherche des attributs via "+cid)
      cid=cid.split("/props")[0]                                         #Au cas ou le nom du fichier aurait été ajouté dans le cid
      ipfs_url="https://ipfs.io/ipfs/"+cid
      if with_ipfs:
        result=api(ipfs_url,timeout=timeout)
        if not result is None:
          if type(result)==dict:
            attr=result["attributes"] if "attributes" in result else ""
            if "description" in result: desc=result["description"]
            if "creators" in result: creators=result["creators"]
          else:
            desc=result
        else:
          log("Echec de récupération de "+ipfs_url)
          desc="metadata non disponibles"
          attr=""

    else:
      #Analyse d'un fichier json d'attribut dans la description onchain
      if attr.startswith("{\""):attr=" - "+attr
      if " - {\"" in attr:
        sections=attr.split(" - {\"")
        desc=sections[0]
        attr="{\""+attr.split(" - {\"")[1]

        _d=json.loads(attr)
        attr=[]
        for k in _d.keys():
          attr.append({"trait_type":k,"value":_d[k]})

    return (attr,desc,tags,creators)


  def get_nft(self,token_id:str,attr=False,transactions=False,with_balance=None,metadata_timeout=3) -> NFT:
    pass


  def complete_collection(self,nfts:[NFT]):
    pass





  def get_nfts(self,_user:AccountOnNetwork,limit=2000,with_attr=False,offset=0,with_collection=False,type_token="NonFungibleESDT,SemiFungibleESDT") -> [NFT]:
    """
    https://docs.multiversx.com/tokens/nft-tokens
    voir
    :param _user:
    :param limit:
    :param with_attr:
    :return:
    """
    pass




  def burn(self,token_id,_user:Key,quantity=1,backup_address=""):
    """
    https://docs.multiversx.com/tokens/nft-tokens#burn-quantity
    :param _user:
    :param token_id:
    :return:
    """
    pass



  def get_token(self,token_id:str) -> dict:
    pass


  def get_min_gas_for_transaction(self,n_transactions=1) -> float:
    return 0.001*n_transactions


  def mint(self, miner:Key, title, description, collection:dict, properties: list,
           storage:Storage, files=[], quantity=1, royalties=0, visual="", tags="", creators=[],
           domain_server="",price=0,symbol="NFluentToken",simulation=False):
    """
    Fabriquer un NFT au standard elrond
    https://docs.elrond.com/tokens/nft-tokens/#nftsft-fields

    l'ajout du domain_server est nécessaire pour respecter l'interface

    :type storage: object
    :param contract:
    :param user_from:
    :param arguments:
    :return:
    """

    pass





  def toAccount(self, user) -> AccountOnNetwork:
    """
    retourne l'objet account pour le réseau
    :param user:
    :return:
    """
    if type(user)==dict:
      if "address" in user:
        user=user["address"]
      else:
        if "address" in user:user=user["address"]

    if type(user)==str:
      user=self.find_key(user)

    if type(user)==Key:
      if user.address=="":
        user.address=UserSecretKey(bytes.fromhex(user.secret_key)).generate_public_key().to_address("erd").bech32()

      _user=self._proxy.get_account(address=Address.from_bech32(user.address))
      _user.secret_key=user.secret_key
      return _user


    # if len(user.split(" "))>10:
    #   secret_key, pubkey = derive_keys(user.strip())
    #   user=self._proxy.get_account(address=Address(pubkey).bech32())
    #   user.secret_key=secret_key.hex()
    #   return user
    #
    # if user.startswith("erd"):
    #   user=self._proxy.get_account(address=user)
    # else:
    #   key=self.find_key(user)
    #   user=self._proxy.get_account(address=Address.from_bech32(key.address))
    #   user.secret_key=key.secret_key

      # pem_file=ELROND_KEY_DIR+user+(".pem" if not user.endswith('.pem') else '')
      # if exists(pem_file):
      #
      #   with open(pem_file,"r") as file:
      #     txt=file.read()
      #     if txt.startswith("-----BEGIN PRIVATE KEY"):
      #       user=UserPEM.from_file(path=Path(pem_file))
      #     else:
      #       words=""
      #       for s in txt.split("\n "):
      #         if len(s)>1:
      #           if " " in s:
      #             words=words+s.split(" ")[1]+" "
      #           else:
      #             words=words+s
      #       words=words.replace("\n","").strip()
      #       secret_key, pubkey = derive_keys(words)
      #       user=self.proxy.get_account(address=Address(pubkey).bech32())
      #       user.secret_key=secret_key.hex()
      # else:
      #   return None

    return user



  def extract_from_tokenid(self, token_id) -> (str,str):
    nonce=""
    collection_id=""

    l_fields=len(token_id.split("-"))
    if l_fields>1:
      collection_id=token_id.split("-")[0]+"-"+token_id.split("-")[1]
    if l_fields>2:
      nonce=token_id.split("-")[2]

    return collection_id,nonce


  def balance(self,account:AccountOnNetwork):
    if type(account)!=AccountOnNetwork: account=self.toAccount(account)
    return self._proxy.get_account(account.address).balance



  def get_keys(self,qrcode_scale=0,address="") -> [Key]:
    """
    retourne l'ensemble des clé ou une seul filtré par l'adresse ou le nom
    :param qrcode_scale:
    :param with_balance:
    :param address:
    :return:
    """
    pass


  def find_key(self,address_or_name) -> Key:
   pass


