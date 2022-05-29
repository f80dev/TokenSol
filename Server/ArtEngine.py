import base64
import os
from io import BytesIO
from os.path import exists
from random import random,seed

import ffmpeg
import requests
from PIL import Image
from PIL.Image import BICUBIC
from PIL.ImageDraw import Draw
from PIL.ImageFont import truetype

from Tools import now, log


class Element():
  name:str
  def __init__(self,name="",ext="png"):
    self.name=name if len(name)>0 else str(int(1000*now()))+str(random()*1000000)
    self.ext=ext

  def fusion(self,to_concat):
    pass

  def save(self,filename):
    pass

  def toStr(self):
    pass




class Sticker(Element):
  image:Image

  def __init__(self,name="",image=None,dimension=None,text:str=None,x:int=None,y:int=None,fontstyle={"color":(0,0,0,255),"size":100,"name":"corbel.ttf"},ext="PNG"):
    super().__init__(name,ext)

    if not image:
      self.image=Image.new("RGBA",dimension)
    else:
      if type(image)==str:
        if not image.startswith("http"):
          if "base64" in image:
            self.image=Image.open(BytesIO(base64.b64decode(image.split("base64,")[1])))
          else:
            self.image=Image.open(image).convert("RGBA")
        else:
          if "/api/images/" in image:
            filename=image.split("/api/images/")[1].split("?")[0]
            f=open("./temp/"+filename,"rb")
            self.image=Image.open(f).convert("RGBA")
            f.close()
          else:
            self.image=Image.open(BytesIO(requests.get(image).content)).convert("RGBA")

        if dimension:self.image=self.image.resize(dimension)

      else:
        if type(image)==bytes:
          self.image=Image.open(BytesIO(image))
        else:
          self.image=image.image.copy()

    if text:
      self.image.info={"name":text}
      self.write(text,x=(x/100)*dimension[0],y=(y/100)*dimension[1],color=fontstyle["color"],size=fontstyle["size"],fontname=fontstyle["name"])

  def write(self,text:str,position="bottom-left",fontname="corbel.ttf",size=22,color=(0,0,0,255),x=None,y=None):
    self.image.info={"name":text}
    font = truetype("./Fonts/"+fontname, size)
    draw=Draw(self.image)
    if x and y:
      draw.text((x,y),text,color,font=font)
    else:
      draw.text((20,self.image.height-30),text,color,font=font)


  def clone(self,new_name=""):
    if new_name=="": new_name=self.name+"_clone"
    return Sticker(new_name,self.image.copy())

  def replace_color(self,old_color,new_color):
    for i in range(0,self.image.size[0]):# process all pixels
      for j in range(0,self.image.size[1]):
        data = self.image.getpixel((i,j))
        if (data==old_color):
          self.image.putpixel((i,j),new_color)

  # def analyse(self):
  #   palette=dict()
  #   for i in range(0,self.image.size[0]):# process all pixels
  #     for j in range(0,self.image.size[1]):
  #       data = self.image.getpixel((i,j))
  #       key=str(data)
  #       palette[key]=palette[key]+1 if key in palette else 0
  #
  #   palette=dict(sorted(palette.items(), key=lambda item: item[1],reverse=True))
  #   return list(palette.keys())[0:5]

  def toBase64(self,format="PNG"):
    buffered = BytesIO()
    self.image.save(buffered, format=format)
    return "data:image/"+format.lower()+";base64,"+str(base64.b64encode(buffered.getvalue()),"utf8")

  def fusion(self,to_concat):
    log("Fusion de "+self.name+" avec "+to_concat.name)
    src:Image=to_concat.image.resize(size=self.image.size,resample=BICUBIC)
    self.image.alpha_composite(src)

  def save(self,filename):
    #voir https://pillow.readthedocs.io/en/stable/handbook/image-file-formats.html#webp pour le Webp
    self.image.save(filename,quality=98,method=6,lossless=True)




class VideoElement(Element):
  video:str

  def __init__(self,video="",name=""):
    super().__init__(name,"mp4")
    self.video=video if len(video)>0 else "c:/temp/"+name+".mp4"
    if not exists(self.video):
      ffmpeg.Stream()

  def flip(self,new_name=""):
    input = ffmpeg.input(self.video)
    audio = input.audio.filter("aecho", 0.8, 0.9, 1000, 0.3)
    video = input.video.hflip()
    if len(new_name)==0:new_name=self.video
    out = ffmpeg.output(audio, video, new_name)
    return out

  def fusion(self,to_concat):
    video1=ffmpeg.input(self.video)
    video2=ffmpeg.input(to_concat.video)
    stream=ffmpeg.concat(video1,video2).output("tmp.mp4").run()
    os.remove(self.video)
    os.rename("tmp.mp4",self.video)


  def toBase64(self):
    f=open(self.video,"rb")
    rc="data:video/mp4;base64,"+str(base64.b16encode(f.read()),"utf8")
    f.close()
    return rc


  def save(self,filename):
    return True

  def toStr(self):
    return self.video




class TextElement(Element):
  text:str

  def __init__(self,name="",text=""):
    super().__init__(name,"txt")
    self.text=text

  def fusion(self,to_concat):
    self.text=self.text + to_concat.text

  def toBase64(self):
    return "data:plain/text;base64,"+str(base64.b16encode(self.text),"utf8")

  def save(self,filename):
    f=open(filename,"w")
    f.writelines(self.text)
    f.close()

  def toStr(self):
    return self.text




class Layer:
  def __init__(self,name="",element=None,width=500,height=500,position=0,unique=False,indexed=True):
    self.elements=[]
    self.name=name if len(name)>0 else str(now())
    self.width=width
    self.unique=unique if type(unique)!=str else False
    self.indexed=indexed if type(indexed)!=str else False
    self.height=height
    self.position=position
    if element:self.add(element)


  def order(self) -> int:
    pass

  def remove(self,img:Element) -> bool:
    if not img in self.elements:return False
    pos=self.elements.index(img)
    del self.elements[pos]
    return True


  def add(self,elt:Element,autoName=True):
    if elt is None: return self
    elt.name=self.name+"-"+str(len(self.elements))
    self.elements.append(elt)
    return self


  # def clone_image(self,old_color,new_colors,index=0):
  #   """
  #   https://pillow.readthedocs.io/en/stable/reference/ImagePalette.html#
  #   :param index:
  #   :return:
  #   """
  #   for new_color in new_colors:
  #     img=Sticker("",self.elements[index])
  #     img.replace_color(old_color,new_color)
  #     self.elements.append(img)
  #
  #   return self


  def save(self,dir:str):
    if not dir.endswith("/"):dir=dir+"/"
    i=0
    for elt in self.elements:
      i=i+1
      elt.save(dir+self.name+"_"+str(i)+".png",overwrite=True)
    return True


  def random(self):
    rc=None
    if len(self.elements)>0:
      pos=int(random()*len(self.elements))
      rc=self.elements[pos]

    return rc



class ArtEngine:
  """
  Moteur de génération
  """
  layers=[]
  #filenames=[]

  def __init__(self,name="collage"):
    self.name=name

  def reset(self):
    self.layers.clear()

  def add(self,layer):
    # if layer.unique and len(self.filenames)==0:
    #   for e in layer.elements:
    #     if "name" in e.image.info:
    #       self.filenames.append(e.image.info["name"])

    l=self.get_layer(layer.name)
    if l is None:
      self.layers.append(layer)
    else:
      pos=self.layers.index(l)
      self.layers[pos]=layer


  def add_image_to_layer(self,name,image):
    layer=self.get_layer(name)
    layer.add(Sticker("",image))

  def sort(self):
    self.layers=sorted(self.layers,key=lambda x:x.position)

  def generate(self,collage:Element,dir="",limit=100,seed_generator=0):
    if seed_generator>0:seed(seed_generator)
    if len(dir)>0 and not dir.endswith("/"):dir=dir+"/"
    rc=list()
    width=0
    height=0
    max_item=1

    self.sort()
    for layer in self.layers:
      width=max(width,layer.width)
      height=max(height,layer.height)
      if layer.indexed:
        max_item=max_item*len(layer.elements)

    histo=[]
    index=0
    limit=min(limit,max_item)
    while index<limit:

      name=[]
      for layer in self.layers:
        log("Ajout d'un élément du calque "+layer.name)
        elt=layer.random() if not layer.unique else layer.elements[0]
        if elt is None:
          log("il n'y a plus assez de NFT pour respecter l'unicité")
          index=limit
          break
        else:
          if layer.indexed:name.append(elt.name)
          collage.fusion(elt)

      if not name in histo and index<limit:
        index=index+1
        if layer.unique: layer.remove(elt)
        histo.append(name)
        if len(dir)>0:
          # if index<len(self.filenames):
          #   filename=dir+self.filenames[index]+"."+collage.ext
          # else:
          filename=dir+self.name+"_"+str(index)+"."+collage.ext if not "__idx__" in self.name else dir+self.name.replace("__idx__",str(index))+"."+collage.ext
          rc.append(filename)
          collage.save(filename)
        else:
          rc.append(collage.toStr())

    return rc




  def get_layer(self, name) -> Layer:
    for l in self.layers:
      if l.name==name:return l
    return None



  def delete(self, name):
    for l in self.layers:
      if l.name==name:
        self.layers.remove(l)






