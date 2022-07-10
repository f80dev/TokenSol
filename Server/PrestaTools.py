import shutil

import requests
import unidecode

from Tools import log
from dict2xml import Dict2XML


class PrestaTools:
  def __init__(self, key, server="161.97.75.165", port="8080"):
    self.key = key
    self.server = server
    self.port = port

  def url(self, service, params=""):
    url = "http://" + self.server + ":" + self.port + "/api/" + service + "?ws_key=" + self.key + "&io_format=JSON" + "&" + params
    log("Ouverture de " + url)
    return url

  def toXML(self, _d: dict, root_label: str):
    return "<prestashop xmlns:xlink=\"http://www.w3.org/1999/xlink\">" + str(
      Dict2XML(root_label, _d).to_xml_string(xml_declaration=False), "utf8") + "</prestashop>"

  def get_languages(self, label):
    return {"language": [{"@attributes": {"id": 1}, "@cdata": label}, {"@attributes": {"id": 2}, "@cdata": label}]}

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
    cats = requests.get(self.url("categories", "display=full")).json()
    for cat in cats["categories"]:
      if cat["name"][0]["value"] == name: return cat
    return None

  def add_category(self, name, parent=None, id=None):
    """
      voir https://devdocs.prestashop.com/1.7/webservice/resources/categories/
      :param name:
      :param parent:
      :param id:
      :return:
      """
    _c = dict()
    _c["name"] = self.get_languages(name)
    _c["link_rewrite"] = self.get_languages(name)
    _c["active"] = {"@cdata": 1}
    _c["statut"] = {"@cdata": 1}
    if id: _c["id"] = {"@cdata": id}
    if parent:
      _c["id_parent"] = {"@cdata": parent}
      _c["is_root_category"] = {"@cdata": 0}
    else:
      _c["is_root_category"] = {"@cdata": 1}

    _c["id_shop_default"] = {"@cdata": 1}
    _c["meta_title"] = self.get_languages(name)
    _c["meta_keywords"] = self.get_languages("NFT")

    resp = requests.post(self.url("categories"), data=self.toXML(_c, "category"),
                         headers={'Content-Type': 'application/xml'}).json()
    return resp["category"]

  def to_cdata(self, _d: dict):
    for k in _d.keys():
      _d[k] = {"@cdata": _d[k]}
    return _d

  def normalize(self, s):
    for i in range(10):
      s = s.replace("#", " ")
    s=unidecode.unidecode(s)
    return s


  def add_product(self, name, category, symbol="", description="", price=0, on_sale=True, properties=dict(),address=""):
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
    _p = self.to_cdata(_p)


    _p["description_short"]=self.normalize(description)

    _p["reference"]={"@cdata":symbol}

    _p["on_sale"] = {"@cdata": 1 if on_sale else 0}
    _p["low_stock_alert"]={"@cdata":0}
    _p["is_virtual"] = {"@cdata": 1}
    _p["customizable"] = {"@cdata": 0}
    _p["active"]= {"@cdata": 1}
    _p["available_for_order"]= {"@cdata": 1}
    _p["available_date"]= {"@cdata": "2022-01-01"}
    _p["price"] = {"@cdata": price}
    if len(address)>0: _p["location"]={"@cdata": address}
    _p["id_category_default"] = {"@cdata": category}
    _p["state"] = {"@cdata": 1}
    _p["wholesale_price"]={"@cdata":price}
    _p["show_price"]={"@cdata":1}
    _p["name"] = self.get_languages(self.normalize(name))

    description=""
    for prop in properties:
      if "value" in prop:
        description=description+prop["trait_type"]+" : "+str(prop["value"])+" - "
    _p["description"]=self.normalize(description)

    xml = self.toXML(_p, "product")
    resp = requests.post(self.url("products"), data=xml, headers={'Content-Type': 'application/xml'})
    try:
      _product = resp.json()["product"]
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
    l_features = requests.get(self.url("product_features", "display=full")).json()["product_features"]
    for feature in l_features:
      if feature["name"][0]["value"] == name:
        return feature

    _f = requests.get(self.url("product_features", "schema=blank")).json()
    _f = dict()
    _f["name"] = self.get_languages(name)
    resp = requests.post(self.url("product_features"), data=self.toXML(_f, "product_feature"),
                         headers={'Content-Type': 'application/xml'})
    return resp.json()["product_feature"]

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



  def add_feature_value(self, feature_id, feature_value):
    _f = requests.get(self.url("product_feature_values", "schema=blank")).json()["product_feature_value"]
    _f["custom"] = 0
    _f["id_feature"]=feature_id
    _f["value"]=self.get_languages(feature_value)
    resp = requests.post(self.url("product_feature_values"), data=self.toXML(_f, "product_feature_value"),
                         headers={'Content-Type': 'application/xml'})
    return resp.json()["product_feature_value"]
