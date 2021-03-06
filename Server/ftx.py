import hmac
import time

import requests
from requests import Request, Session

from Tools import log
from settings import FTX_API_KEY, FTX_API_SECRET


class FTX:
  def __init__(self, endpoint="https://ftx.us/api",api_key=FTX_API_KEY,secret_key=FTX_API_SECRET):
    self.endpoint = endpoint + "/"
    self.session=Session()
    self.api_key=api_key
    self.secret_key=secret_key

  def api(self, service, method="GET", timeout=0):
    """
    voir https://docs.ftx.us/?python#authentication
    :param service:
    :param method:
    :return:
    """

    ts = int(time.time()*1000)
    url = self.endpoint + service
    if timeout > 0: url = url + ("&" if "?" in url else "?") + "end_time=" + str(int(ts / 1000) + timeout)
    log("Appel de "+url)
    request = Request(method, url)
    prepared = request.prepare()

    s=prepared.path_url[prepared.path_url.rindex("/"):]
    signature_payload = f'{ts}{prepared.method}{s}'
    if prepared.body: signature_payload += prepared.body
    signature_payload = signature_payload.encode()

    signature = hmac.new(self.secret_key.encode(), signature_payload, 'sha256').hexdigest()

    prepared.headers[f'FTX-KEY'] = self.api_key
    prepared.headers[f'FTX-SIGN'] = signature
    prepared.headers[f'FTX-TS'] = str(ts)

    resp=requests.get(url,headers=prepared.headers)

    return resp


  def collections(self, filter: str = ""):
    resp = self.api("nft/collections", timeout=10)
    rc = list()
    for col in resp.json()["result"]:
      if len(filter) == 0 or col["collection"].lower().startswith(filter.lower()):
        rc.append(col)

    log(str(len(rc)) + " collections")
    return rc


  def account(self):
    result=self.api("account").json()
    return result


  def nfts(self, service="fills", key="", value="", out="", timeout=0):
    """
        https://docs.ftx.com/?python#list-nfts
        :param key:
        :param value:
        :return:
        """
    result = self.api("nft/" + service, timeout=timeout)
    rc = list()

    operator = "="
    if value.startswith("!"):
      value = value[1:]
      operator = "!="

    if result.status_code != 200:
      return {"status": result.status_code, "message": str(result.content,"utf8")}

    for nft in result.json()["result"]:
      if len(key) > 0:
        compare_value = nft[key] if (nft[key] is not None) else "none"
        if type(compare_value) != str: compare_value = str(compare_value).lower()
      else:
        compare_value = ""

      if len(value) == 0 or len(key) == 0 or (compare_value in value and operator == "=") or (
        not compare_value in value and operator == "!="):
        if len(out) == 0:
          rc.append(nft)
        else:
          new_nft = dict()
          for k in out.split(","):
            new_nft[k] = nft[k]
          rc.append(new_nft)

    return {"status_code":200,"results":rc}


  def get_nfts_balances(self):
    rc=self.api("nft/balances")
    if rc.status_code==401:
      return []
    else:
      return rc.result
