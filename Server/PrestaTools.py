import shutil

import requests
import unidecode
import xmltodict

from Tools import log


class PrestaTools:
  def __init__(self, key, server="http://161.97.75.165:8080/",language=1):
    self.key = key
    self.server = server
    self.language=language

  def url(self, service, params=""):
    url =  self.server + "api/" + service + "?ws_key=" + self.key + "&io_format=JSON" + "&" + params
    #log("Ouverture de " + url)
    return url

  def toXML(self, _d: dict, root_label: str,entete=True,pretty=True):
    rc="<prestashop xmlns:xlink=\"http://www.w3.org/1999/xlink\">" if entete else ""
    _d={root_label:_d}
    xml=xmltodict.unparse(_d,pretty=pretty,full_document=False)
    rc=rc+xml
    if entete:rc=rc+"</prestashop>"
    return rc

  def get_languages(self, label):
    if self.language==0:
      return label
    else:
      rc=[]
      for i in range(1,self.language+1):
        rc.append({"language":{"@id": i,"#text": label}})
      return rc


  def add_image(self, product_id, url="", filename="./temp/image.gif"):
    """"
      voir https://www.h-hennes.fr/blog/2021/03/12/prestashop-gerer-les-images-produits-via-lapi/
      https://devdocs.prestashop.com/1.7/webservice/resources/image_types/

      """

    f = None
    if url.startswith("http") == str:
      f = open(filename, "wb")
      res = requests.get(url, stream=True)
      shutil.copyfileobj(res.raw, f)
      f.seek(0)
    else:
      filename = url

    files = {
      "name": filename,
      "image": open(filename, "rb"),
      "type": "image/gif"
    }
    resp = requests.post(self.url("images/products/" + product_id), files=files)
    try:
      resp = resp.json()
      return resp["image"]
    except:
      log("Erreur d'upload de l'image " + str(resp))
      return None



  def find_category(self, name):
    cats = requests.get(self.url("categories", "display=full"))
    for cat in cats.json()["categories"]:
      if self.language==1:
        if cat["name"] == name: return cat
      else:
        if cat["name"][0]["value"] == name: return cat
    return None



  def add_product_category(self,id_product,id_categorie):
    resp = requests.get(self.url("categories/products/"+str(id_product),"schema=blank"))
    pass


  def add_product_to_category(self, name, products):
    _c=self.find_category(name)
    if not "associations" in _c: _c["associations"]={"products":[]}
    for product in products:
      _c["associations"]["products"].append({"product":{"id":product}})
    resp = requests.put(self.url("categories"), data=self.toXML(_c, "category")).json()
    return resp["category"]


  def add_category(self, name, parent=None,description=""):
    """
      voir https://devdocs.prestashop.com/1.7/webservice/resources/categories/
      :param name:
      :param parent:
      :param id:
      :return:
      """
    _c = requests.get(self.url("categories","schema=blank")).json()["category"]
    del _c["id"]

    if len(description)==0:description=name
    _c["name"] = self.get_languages(self.normalize(name))
    _c["description"] = self.get_languages(self.normalize(description))
    _c["link_rewrite"] = self.get_languages(self.normalize(name))
    _c["active"] = 1

    if parent:
      _c["id_parent"] = parent
      _c["is_root_category"] = 0
    else:
      _c["is_root_category"] = 1

    #_c["description"] = self.get_languages(self.normalize(name))
    # _c["id_shop_default"] = {"@cdata": 1}

    resp = requests.post(self.url("categories"), data=self.toXML(_c, "category")).json()
    return resp["category"]



  def to_cdata(self, _d: dict):
    for k in _d.keys():
      _d[k] = {"@cdata": _d[k]}
    return _d



  def normalize(self, s):
    for i in range(10):
      s = s.replace("#", "n")
    s=unidecode.unidecode(s)
    return s


  def get_products(self,id:str=""):
    if id:id=str(id)
    rest = requests.get(self.url("products/"+id,"display=full")).json()["products"]
    if len(id)>0 and len(rest)>0:return rest[0]
    return rest["products"]

  def get_images(self):
    rest = requests.get(self.url("images/products/5","display=full")).json()
    return rest["images"]

  def get_product_categories(self,product_id=""):
    rest = requests.get(self.url("categories/products/"+product_id,"display=full"))
    return rest.json()["categories"]

  def cdata(self,txt):
    return "![CDATA["+str(txt)+"]]"


  def get_product_feature(self,id_feature,id_feature_value):
    for feature in requests.get(self.url("product_features", "display=full")).json()["product_features"]:
      if feature["id"]==int(id_feature):
        for feature_value in requests.get(self.url("product_feature_values", "display=full")).json()["product_feature_values"]:
          if feature_value["id"]==int(id_feature_value):
            return (feature["name"],feature_value["value"])
    return None


  def add_product(self, name, category, symbol="", description="", price=0, on_sale=True, properties=dict(),features=dict(),tags=list()):
    """
      voir https://devdocs.prestashop.com/1.7/webservice/resources/products/
      :param name:
      :param category:
      :param image:
      :param quantity:
      :param symbol:
      :param description:
      :param price:
      :return:
      """
    _p = requests.get(self.url("products", "schema=blank")).json()["product"]
    del _p["id"]
    del _p["position_in_category"]
    del _p["associations"]

    _p["description_short"]=self.get_languages(self.normalize(description))
    _p["reference"]=symbol
    _p["on_sale"] =1 if on_sale else 0
    _p["low_stock_alert"]=0
    _p["minimal_quantity"]=1
    _p["is_virtual"] = 1
    _p["customizable"] = 0
    _p["active"]= 1
    _p["available_for_order"]= 1
    #_p["available_date"]= "2022-01-01"
    _p["price"] = price

    _category=self.find_category(category)
    _p["id_category_default"] = _category["id"]

    log("Remplissage de l'associations")
    _p["associations"]={
      "product_features":[]
    }
    l_features=[]
    for feature in features.keys():
      log("Insertion de "+feature)
      _feature=self.add_product_feature(feature)
      _feature_value=self.add_feature_value(None,feature,features[feature])
      if _feature_value:
        l_features.append({"id":_feature["id"],"id_feature_value":int(_feature_value["id"])})
    _p["associations"]["product_features"]={"product_feature":l_features}

    _p["state"] = 1
    _p["wholesale_price"]=price
    _p["show_price"]=1
    _p["name"] = self.get_languages(self.normalize(name))

    description=""
    for prop in properties:
      if "value" in prop:
        description=description+prop["trait_type"]+" : "+str(prop["value"])+" - "
    _p["description"]=self.get_languages(self.normalize(description))

    xml = self.toXML(_p, "product")
    resp = requests.post(self.url("products"), data=xml, headers={'Content-Type': 'application/xml'})
    if resp.status_code==400:
      log("xml="+xml)
      log("Probleme de traduction "+resp.text)
    try:
      _product = resp.json()["product"]
      #self.add_product_to_category(category,[_product["id"]])
      return _product
    except:
      log("Erreur de creation")
      return None


  def add_product_feature(self, name):
    """
      voir https://devdocs.prestashop.com/1.7/webservice/resources/product_features/
      et https://devdocs.prestashop.com/1.7/webservice/resources/product_feature_values/
      :param name:
      :return:
      """
    l_features = requests.get(self.url("product_features", "display=full")).json()
    if len(l_features)>0:
      for feature in l_features["product_features"]:
        if feature["name"] == name:
          return feature

    _f = requests.get(self.url("product_features", "schema=blank")).json()
    _f = dict()
    _f["name"] = self.get_languages(name)
    resp = requests.post(self.url("product_features"), data=self.toXML(_f, "product_feature"),
                         headers={'Content-Type': 'application/xml'})
    return resp.json()["product_feature"]

  def add_product_option(self, name):
    """
      voir https://devdocs.prestashop.com/1.7/webservice/resources/product_options/
      et https://devdocs.prestashop.com/1.7/webservice/resources/product_options_values/
      :param name:
      :return:
      """
    l_features = requests.get(self.url("product_options", "display=full")).json()
    if len(l_features)>0:
      for feature in l_features["product_options"]:
        if feature["name"] == name:
          return feature

    _f = requests.get(self.url("product_options", "schema=blank")).json()
    _f["name"] = self.get_languages(name)
    _f["public_name"]=self.get_languages(name)
    _f["group_type"]={"@cdata": 0}
    resp = requests.post(self.url("product_options"), data=self.toXML(_f, "product_option"),
                         headers={'Content-Type': 'application/xml'})
    return resp.json()["product_option"]


  def set_product_quantity(self, product, quantity=1, id_shop=1):
    """
      voir  https://devdocs.prestashop.com/1.7/webservice/resources/stock_availables/
            https://www.prestashop.com/forums/topic/229629-webservice-how-to-set-product-quantity/
      :param product:
      :param quantity:
      :return:
      """
    stock = requests.get(self.url("stock_availables", "schema=blank")).json()["stock_available"]
    stock["id"] = product["associations"]["stock_availables"][0]["id"]
    stock["id_product"] = product["id"]
    stock["id_product_attribute"] = product["associations"]["stock_availables"][0]["id_product_attribute"]
    stock["quantity"] = quantity
    stock["id_shop"] = id_shop
    stock["out_of_stock"] = quantity
    stock["depends_on_stock"] = 0
    resp = requests.put(self.url("stock_availables/" + stock["id"]), self.toXML(stock, "stock_available"))
    return resp.json()



  def add_feature_value(self,id_product, feature_name,feature_value):
    """
    https://devdocs.prestashop.com/1.7/webservice/resources/product_feature_values/
    :param id_product:
    :param feature_name:
    :param feature_value:
    :return:
    """
    if len(feature_value)==0: return None

    feature=self.add_product_feature(feature_name)
    _fs = requests.get(self.url("product_feature_values", "display=full")).json()
    if len(_fs)>0:
      for _f in _fs["product_feature_values"]:
        if int(_f["id_feature"])==feature["id"] and _f["value"]==feature_value:
          return _f

    _f = requests.get(self.url("product_feature_values", "schema=blank")).json()["product_feature_value"]
    _f["custom"] = 1
    _f["id_feature"]=feature["id"]
    _f["value"]=self.get_languages(feature_value)
    if id_product:
      resp=requests.post(self.url("product_feature_values/product/"+str(id_product)),data=self.toXML(_f,"product_feature_value"),headers={'Content-Type': 'application/xml'})
    else:
      resp=requests.post(self.url("product_feature_values"),data=self.toXML(_f,"product_feature_value"),headers={'Content-Type': 'application/xml'})
    return resp.json()["product_feature_value"]


  def add_option_value(self,id_product, option_name,option_value):
    if len(option_value)==0: return None

    option=self.add_product_option(option_name)
    _f = requests.get(self.url("product_option_values", "schema=blank")).json()["product_option_value"]
    _f["custom"] = 0
    _f["id_option"]=option["id"]
    _f["value"]=self.get_languages(option_name)
    resp=requests.post(self.url("product_option_values/products/"+str(id_product)),data=self.toXML(_f,"feature_value"),headers={'Content-Type': 'application/xml'})
    return resp.json()["product_option_value"]




  def find_category_in_collections(self,category_name , collections):
    for col_from_op in collections:
      if col_from_op["name"]==category_name:
        return col_from_op
    return None

  def get_categories(self, id_category=None):
    _cs=requests.get(self.url("categories","display=full")).json()["categories"]
    if id_category is None: return _cs
    for _c in _cs:
      if _c["id"]==int(id_category):
        return _c
    return None

  def desc_to_dict(self, description:str):
    rc=dict()
    for l in description.split(" - "):
      rc[l.split(" : ")[0]]=l.split(" : ")[1]
    return rc

  def edit_customer(self, customer_id, field, value):
    customers=requests.get(self.url("customers/"+str(customer_id),"display=full")).json()["customers"]
    if len(customers)>0:
      _c=customers[0]
      _c[field]=value
      #_c["id"]=str(customer_id)
      _c["associations"]["groups"]={"group":_c["associations"]["groups"]}
      xml=self.toXML(_c,"customer",True,False)

      resp=requests.put(self.url("customers/"+str(customer_id)),xml)
      return (resp.status_code==200)
    else:
      return False





