import base64
import os
from io import BytesIO
from os.path import exists
from random import random,seed

import cairo
import ffmpeg
import imageio
import numpy
import numpy as np
import requests
from PIL import Image, ImageSequence
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

  def save(self,filename,quality=98):
    pass

  def toStr(self):
    pass




class Sticker(Element):
  image:Image=None
  frames=[]
  text:dict=None

  def __init__(self,name="",image=None,dimension=None,text:str=None,x:int=None,y:int=None,fontstyle={"color":(0,0,0,255),"size":100,"name":"corbel.ttf"},ext="PNG"):
    super().__init__(name,ext)

    if image:
      if type(image)==str:
        if not image.startswith("http"):
          if "base64" in image:
            self.image=Image.open(BytesIO(base64.b64decode(image.split("base64,")[1])))
          else:
            self.image=Image.open(image).convert("RGBA")
        else:
          if "/api/images/" in image:
            filename=image.split("/api/images/")[1].split("?")[0]
            self.image=Image.open("./temp/"+filename)
            if self.image and self.image.mode!="RGBA":self.image=self.image.convert("RGBA")
          else:
            self.image=Image.open(BytesIO(requests.get(image).content)).convert("RGBA")

      else:
        if type(image)==bytes:
          self.image=Image.open(BytesIO(image))
        else:
          self.image=image.copy()

    if text:
      self.text={
        "text":text,
        "fontstyle":fontstyle,
        "dimension":dimension,
        "x":x,"y":y
      }

    if not text and not image:
      self.image=Image.new("RGBA",dimension)


  def render_text(self,factor=1):
    dimension=(int(self.text["dimension"][0]*factor),int(self.text["dimension"][1]*factor))

    self.image=Image.new("RGBA",dimension)
    self.image.info={"name":self.text["text"]}
    fontstyle=self.text["fontstyle"]
    self.write(
      self.text["text"],
      x=(self.text["x"]/100)*dimension[0],y=(self.text["y"]/100)*dimension[1],
      color=fontstyle["color"],
      size=int((fontstyle["size"]/100)*dimension[0]),
      fontname=fontstyle["name"]
    )
    return self.image


  def render_svg(self,dictionnary:dict={}):
    svg_code=self.text
    for k in dictionnary.keys():
      svg_code=svg_code.replace(k,dictionnary[k])

    with cairo.SVGSurface(svg_code,self.text["dimension"][0],self.text["dimension"][1]) as surface:
      buffered = BytesIO()
      surface.write_to_png(buffered)
      self.image.save(buffered, format="WEBP",quality=90)
    return self.image

  def clear(self):
    if self.text :
      self.image=None

  def open(self):
    if self.image and self.image.readonly==0:
      self.image=Image.open(self.image.filename)

  def close(self):
    if self.image:
      self.image.close()

  def delete(self):
    if self.image:
      os.remove(self.image.filename)

  def write(self,text:str,position="bottom-left",fontname="corbel.ttf",size=22,color=(0,0,0,255),x=None,y=None):
    font = truetype("./Fonts/"+fontname, size)

    self.image.info={"name":text}

    draw=Draw(self.image)
    if x and y:
      draw.text((x,y),text,color,font=font)
    else:
      draw.text((20,self.image.height-30),text,color,font=font)

    return self.image


  def clone(self,new_name=""):
    if new_name=="": new_name=self.name+"_clone"
    return Sticker(name=new_name,image=self.image.copy())

  def replace_color(self,old_color,new_color):
    if old_color.startswith("#"):old_color=(int(old_color[1:2],16),int(old_color[3:4],16),int(old_color[5:6],16))
    if new_color.startswith("#"):new_color=(int(new_color[1:2],16),int(new_color[3:4],16),int(new_color[5:6],16))

    data = np.array(self.image)
    red, green, blue, alpha = data.T
    replacement_area = (red == old_color[0]) & (blue == old_color[2]) & (green == old_color[1])
    data[..., :-1][replacement_area.T] = (new_color[0], new_color[2], new_color[1])

    return Image.fromarray(data,"RGBA")


  def toBase64(self,format="WEBP",factor=1,quality=98):
    buffered = BytesIO()
    if self.image is None and self.text is not None:
      self.render_text(factor)

    self.image.save(buffered, format=format,quality=quality)
    self.clear()
    return "data:image/"+format.lower()+";base64,"+str(base64.b64encode(buffered.getvalue()),"utf8")


  def merge_animated_image(self,base:Image,to_paste:Image):
    filename="./temp/temp"+str(now())+".gif"
    wr=imageio.get_writer(filename,mode="I")

    frames_to_paste = [f.convert("RGBA").resize(base.size) for f in ImageSequence.Iterator(to_paste)]
    frame_base=[f.convert("RGBA") for f in ImageSequence.Iterator(base)]
    for i,frame in enumerate(frames_to_paste):
      if i<len(frame_base):
        frame_base[i].alpha_composite(frame)
      else:
        #Il y a plus assez d'image dans la base donc on ajoute les images a coller
        frame_base.append(frame)

      ndarray=numpy.asarray(frame_base[i])
      wr.append_data(ndarray)

    wr.close()
    rc=Image.open(filename)
    rc.load()
    return rc


  def convert_image_to_animated(self,base:Image,n_frames:int):
    filename="./temp/temp"+str(now())+".gif"

    wr=imageio.get_writer(filename,mode="I")
    for i in range(n_frames):
      ndarray=numpy.asarray(base)
      wr.append_data(ndarray)
    wr.close()

    rc= Image.open(filename)
    return rc


  def fusion(self,to_concat,factor):
      #log("Fusion de "+self.name+" avec "+to_concat.name)
      if to_concat.image is None and not to_concat.text is None:
        if "<svg" in to_concat.text:
          src=to_concat.render_svg()
        else:
          src=to_concat.render_text(factor)

      if self.image and to_concat.image:
        if (to_concat.image.format=="WEBP" or to_concat.image.format=="GIF") and to_concat.image.is_animated:
          if self.image.format is None:
            #Convert to animated
            self.image=self.convert_image_to_animated(self.image.copy(),to_concat.image.n_frames)

          #Décomposition de l'image a coller
          self.image=self.merge_animated_image(self.image,to_concat.image)

        else:
          if self.image.format is None:
            self.image.alpha_composite(to_concat.image.resize(self.image.size))
          else:
            self.image=self.merge_animated_image(self.image.copy(),to_concat.image)

        return True

      return False





  def save(self,filename,quality=98):
    #voir https://pillow.readthedocs.io/en/stable/handbook/image-file-formats.html#webp pour le Webp
    if self.text and self.text["text"] and "<svg" in self.text["text"]:
      f=open(filename,"w")
      f.writelines(self.text["text"])
      f.close()
    else:
      if not self.image.format is None and self.image.is_animated:
        frames = [f.convert("RGBA") for f in ImageSequence.Iterator(self.image)]
        frames[0].save(filename,append_images=frames[1:],save_all=True)
      else:
        self.image.save(filename,quality=int(quality),method=6,lossless=(quality==100),save_all=True)

      self.image.close()
      if self.image.format and self.image.filename: os.remove(self.image.filename)




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
  def __init__(self,name="",element=None,position=0,unique=False,indexed=True):
    self.elements=[]
    self.name=name if len(name)>0 else str(now())
    self.unique=unique if type(unique)!=str else False
    self.indexed=indexed if type(indexed)!=str else False
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

  def generate(self,collage:Element,dir="",limit=100,seed_generator=0,width=500,height=500,quality=100):
    if seed_generator>0:seed(seed_generator)
    if len(dir)>0 and not dir.endswith("/"):dir=dir+"/"
    rc=list()
    max_item=1

    self.sort()

    histo=[]
    index=0
    log("Lancement de la génération de "+str(limit)+" images")
    while index<limit:

      name=[]
      log("NFT "+str(index)+"/"+str(limit)+" généré")
      for layer in self.layers:
        if len(layer.elements)==0:
          elt=None
        else:
          elt=layer.random() if not layer.unique else layer.elements[0]

        if elt is None:
          log("il n'y a plus assez de NFT pour respecter l'unicité")
          index=limit
          break
        else:
          if layer.indexed or layer.unique: name.append(elt.name)
          factor=1 if elt.text is None else width/elt.text["dimension"][0]
          elt.open()
          collage.fusion(elt,factor)
          if layer.unique: layer.remove(elt)
          elt.close()

          if elt.image.format and elt.image.filename.startswith("./temp/temp"):
            elt.delete()

      if not name in histo and index<limit:
        index=index+1

        histo.append(name)
        if len(dir)>0:
          # if index<len(self.filenames):
          #   filename=dir+self.filenames[index]+"."+collage.ext
          # else:
          filename=dir+self.name+"_"+str(index)+"."+collage.ext if not "__idx__" in self.name else dir+self.name.replace("__idx__",str(index))+"."+collage.ext
          rc.append(filename)
          collage.save(filename,quality)
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
