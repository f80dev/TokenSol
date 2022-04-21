import base64
import json
from datetime import datetime

import requests

from Tools import log


class GithubStorage:
	def __init__(self,repo_slug, branch, user,token):
		self.token=token
		self.repo_slug=repo_slug
		self.branch=branch
		self.user=user

	def push_to_repo_branch(self,gitHubFileName, fileName):
		'''
		Push file update to GitHub repo

		:param gitHubFileName: the name of the file in the repo
		:param fileName: the name of the file on the local branch
		:param repo_slug: the github repo slug, i.e. username/repo
		:param branch: the name of the branch to push the file to
		:param user: github username
		:param token: github user token
		:return None
		:raises Exception: if file with the specified name cannot be found in the repo
		'''

		message = "Automated update " + str(datetime.datetime.now())
		path = "https://api.github.com/repos/%s/branches/%s" % (self.repo_slug, self.branch)

		r = requests.get(path, auth=(self.user,self.token))
		if not r.ok:
			print("Error when retrieving branch info from %s" % path)
			print("Reason: %s [%d]" % (r.text, r.status_code))
			raise
		rjson = r.json()
		treeurl = rjson['commit']['commit']['tree']['url']
		r2 = requests.get(treeurl, auth=(self.user,self.token))
		if not r2.ok:
			log("Error when retrieving commit tree from " + treeurl)
			log("Reason: " + r2.text + " "+str(r2.status_code))
			raise
		r2json = r2.json()
		sha = None

		for file in r2json['tree']:
			# Found file, get the sha code
			if file['path'] == gitHubFileName:
				sha = file['sha']

		# if sha is None after the for loop, we did not find the file name!
		if sha is None:
			log("Could not find " + gitHubFileName + " in repos 'tree' ")
			raise Exception

		with open(fileName) as data:
			content = base64.b64encode(data.read())

		# gathered all the data, now let's push
		inputdata = {}
		inputdata["path"] = gitHubFileName
		inputdata["branch"] = self.branch
		inputdata["message"] = message
		inputdata["content"] = content
		if sha:
			inputdata["sha"] = str(sha)

		updateURL = "https://api.github.com/repos/EBISPOT/RDF-platform/contents/" + gitHubFileName
		try:
			rPut = requests.put(updateURL, auth=(self.user,self.token), data = json.dumps(inputdata))
			if not rPut.ok:
				log("Error when pushing to " + updateURL)
				#print("Reason: %s [%d]" % (rPut.text, rPut.status_code))
				raise Exception
		except requests.exceptions.RequestException as e:
			log('Something went wrong! I will print all the information that is available so you can figure out what happend!')
			log(rPut)
			log(rPut.headers)
			log(rPut.text)
