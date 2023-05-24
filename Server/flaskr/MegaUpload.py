import base64
from io import FileIO

from flaskr.Storage import Storage
from mega import Mega

from flaskr.Tools import now
from flaskr.secret import MEGAUPLOAD_EMAIL, MEGAUPLOAD_PASSWORD


class MegaUpload (Storage) :
	work_dir="./temp"
	directory=""

	def __init__(self,email=MEGAUPLOAD_EMAIL,password=MEGAUPLOAD_PASSWORD,directory="TokenForge"):
		self.client = Mega().login(email, password)
		self.directory=directory
		if self.client.find(directory) is None:	self.client.create_folder(directory)

	def add(self,file,overwrite=False):
		filename=now("rand")
		if type(file)==dict:
			filename=file["filename"]
			file=file["content"] if "content" in file else file["file"]
		if type(file)==str:
			if file.startswith("http"): return {"cid":"","url":file}
			if "base64" in file: file=base64.b64decode(file.split("base64,")[1])
		if type(file)==bytes:
			f=open(self.work_dir+"/"+filename,"wb")
			f.write(file)
			f.close()
			file=f.name
		h=self.client.upload(file,dest="/"+self.directory,dest_filename=filename)
		link=self.client.get_link(h)
		return {"cid":h["h"],"url":link}

