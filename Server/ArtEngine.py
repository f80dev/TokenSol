from random import random
from PIL import Image
from PIL.ImageDraw import Draw
from PIL.ImageFont import truetype

from Tools import now


class Sticker():

  image:Image
  name:str

  def __init__(self,name,image=None,dimension=None):
    self.name=name if len(name)>0 else str(int(now()))

    if not image:
      self.image=Image.new("RGBA",dimension)
    else:
      if type(image)==str:
        self.image=Image.open(image).convert("RGBA")
        if dimension:self.image=self.image.resize(dimension)
      else:
        self.image=image.image.copy()


  def write(self,text:str,position="bottom-left",fontname="corbel.ttf",size=22,color=(255,255,255,255)):
    font = truetype(fontname, size)
    draw=Draw(self.image)
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

  def analyse(self,limit=0):
    palette=dict()
    for i in range(0,self.image.size[0]):# process all pixels
      for j in range(0,self.image.size[1]):
        data = self.image.getpixel((i,j))
        key=str(data)
        palette[key]=palette[key]+1 if key in palette else 0

    palette=dict(sorted(palette.items(), key=lambda item: item[1],reverse=True))
    return list(palette.keys())[0:5]


class Layer:
  def __init__(self,name="",sticker=None,width=500,height=500):
    self.stickers=[]
    self.name=name
    self.width=width
    self.height=height
    if sticker:self.add(sticker)


  def order(self) -> int:
    pass


  def add(self,sticker:Sticker):
    self.stickers.append(sticker)
    return self


  def clone_image(self,old_color,new_colors,index=0):
    """
    https://pillow.readthedocs.io/en/stable/reference/ImagePalette.html#
    :param index:
    :return:
    """
    for new_color in new_colors:
      img=Sticker("",self.stickers[index])
      img.replace_color(old_color,new_color)
      self.stickers.append(img)

    return self


  def save(self,dir:str):
    if not dir.endswith("/"):dir=dir+"/"
    i=0
    for image in self.stickers:
      i=i+1
      filename=dir+self.name+"_"+str(i)+".png"
      rc=image.save(filename,overwrite=True)


  def random(self):
    return self.stickers[int(random()*len(self.stickers))]



class ArtEngine:
  layers=[]

  def __init__(self,name="collage"):
    self.name=name

  def add(self,layer):
    self.layers.append(layer)

  def generate(self,dir,limit=100):
    if not dir.endswith("/"):dir=dir+"/"
    width=0
    height=0
    for layer in self.layers:
      width=max(width,layer.width)
      height=max(height,layer.height)

    histo=[]
    index=0
    while index<limit:
      collage = Image.new("RGBA", (width,height), color=(255,255,255,255))
      filename=dir+self.name+"_"+str(index)+".png"

      name=[]
      for layer in self.layers:
        img=layer.random()
        name.append(img.name)
        collage.alpha_composite(img.image)

      if not name in histo:
        index=index+1
        collage.save(filename,overwrite=True)






