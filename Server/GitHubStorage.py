from hashlib import md5
from json import dumps, dump

from github import Github

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

  def add(self,data:dict,id):
    r = Github(self.token).get_user(self.login).get_repo(self.repo)
    content=dumps(data)
    if id is None:id=hex(hash(content))
    try:
      contents = r.get_contents(id,ref=self.branch)
    except:
      r.create_file(id,"test",content,"main")

    return {"cid":id,"url":"https://raw.githubusercontent.com/"+self.login+"/"+self.repo+"/"+self.branch+"/"+id}



