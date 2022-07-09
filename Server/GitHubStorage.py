from hashlib import md5
from json import dumps, dump

from github import Github

from Tools import log


class GithubStorage:
  """
  Stockage sur Github
  https://pygithub.readthedocs.io/en/latest/examples/Repository.html#create-a-new-file-in-the-repository
  """
  def __init__(self,repo, branch, login,token):
    self.token=token
    self.repo=repo
    self.branch=branch
    self.login=login


  def add(self,data:dict,id,overwrite=False):
    r = Github(self.token).get_user(self.login).get_repo(self.repo)
    content=dumps(data)

    if id is None or len(id)==0:id=hex(hash(content))
    if "/" in id:id=id[id.rindex("/")+1:]

    url="https://raw.githubusercontent.com/"+self.login+"/"+self.repo+"/"+self.branch+"/"+id
    log("Ecriture de "+url)

    try:
      if overwrite:
        ct = r.get_contents(id,ref=self.branch)
        result=r.update_file(ct.path,"maj",content,ct.sha,self.branch)
      else:
        contents = r.get_contents(id,ref=self.branch)
    except Exception as inst:
      #log("Probleme de mise a jour / creation "+str(inst.args))
      r.create_file(id,"create",content,self.branch)


    return {"cid":id,"url":url}



