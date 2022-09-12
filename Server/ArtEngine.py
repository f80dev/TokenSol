import base64
import io
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
from PIL import Image, ImageSequence, ImageFilter, ImageOps,ImageEnhance
from PIL.ImageDraw import Draw
from PIL.ImageFont import truetype

from Tools import now, log

def convert_to_gif(content:str,storage_platform=None,filename=None):
  if content.startswith("http"):
    image:Image=Image.open(io.BytesIO(requests.get(content).content))
  else:
    image:Image=Image.open(io.BytesIO(base64.b64decode(content.split("base64,")[1])))

  if filename:
    buffered=open(filename,"wb")
  else:
    buffered =io.BytesIO()

  if image.is_animated:
    frames = [f.convert("RGBA") for f in ImageSequence.Iterator(image)]
    frames[0].save(buffered,format="GIF",save_all=True,append_images=frames[1:],optimize=True,quality=90)
  else:
    image.save(buffered, format="GIF",quality=90)

  if storage_platform:
    url=storage_platform.add(bytes(buffered.getvalue()),"image/gif")["url"]
    return url

  if filename:
    buffered.close()
    return filename

  return buffered




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

  def __init__(self,name="",image=None,
               dimension=None,text:str=None,x:int=None,y:int=None,
               fontstyle={"color":(0,0,0,255),"size":100,"name":"corbel.ttf"},
               ext="WEBP",data=""):
    super().__init__(name,ext)
    self.data=data

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
    if not self.image is None:
      if self.image.readonly==0 and self.image.format:
        if self.image.filename!="":
          self.image=Image.open(self.image.filename)
        else:
          if self.image.fp:
            self.image.fp.open()


  def close(self):
    if self.image and self.image.format and self.image.filename!="":
      self.image.close()

  def delete(self):
    try:
      os.remove(self.image.filename)
      return True
    except:
      return False

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
    filename="./temp/temp_merge_"+str(now())+".gif"
    wr=imageio.get_writer(filename,mode="I")

    frames_to_paste = [f.resize(base.size).convert("RGBA") for f in ImageSequence.Iterator(to_paste)]
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
    to_paste.close()
    rc=Image.open(filename,"r")
    return rc


  def convertImageFormat(self,imgObj, outputFormat=None):
    newImgObj = imgObj
    if outputFormat and (imgObj.format != outputFormat):
      imageBytesIO = BytesIO()
      imgObj.save(imageBytesIO, outputFormat)
      newImgObj = Image.open(imageBytesIO)

    return newImgObj


  def convert_image_to_animated(self,base:Image,n_frames:int):
    filename="./temp/temp_convert_"+str(now())+".gif"

    base=self.convertImageFormat(base,"GIF")
    images=[base]*(n_frames-1)

    images[0].save(filename, save_all=True,append_images=images[1:],disposal=2,loop=0)
    base.close()

    for image in images:
      image.close()

    # wr=imageio.get_writer(filename,mode="I")
    # cp=base.convert("RGBA")
    # ndarray=numpy.asarray(cp)
    # for i in range(n_frames):
    #   wr.append_data(ndarray.copy())
    # wr.close()
    #
    # base.close()
    rc= Image.open(filename)
    return rc


  def fusion(self,to_concat,factor):
      #log("Fusion de "+self.name+" avec "+to_concat.name)
      if to_concat.image is None and not to_concat.text is None:
        if "<svg" in to_concat.text:
          log("Collage d'un SVG")
          src=to_concat.render_svg()
        else:
          log("Collage d'un texte")
          src=to_concat.render_text(factor)

      if self.image and to_concat.image:
        if (to_concat.image.format=="WEBP" or to_concat.image.format=="GIF") and to_concat.image.is_animated:
          if self.image.format is None:
            log("Convertion de la base en image animé")
            self.image=self.convert_image_to_animated(self.image,to_concat.image.n_frames)

          log("Collage d'une image animé sur la base")
          self.image=self.merge_animated_image(self.image,to_concat.image)
          to_concat.image.close()

        else:
          log("Collage d'une image fixe ...")
          if self.image.format is None:
            log("... sur la base fixe")
            self.image.alpha_composite(to_concat.image.resize(self.image.size))
          else:
            log("... sur une base animé")
            to_concat.image=self.convert_image_to_animated(to_concat.image,self.image.n_frames)
            self.image=self.merge_animated_image(self.image,to_concat.image)
            to_concat.image.close()






  def save(self,filename,quality=98,index=0):
    #voir https://pillow.readthedocs.io/en/stable/handbook/image-file-formats.html#webp pour le Webp
    _data_to_add=self.data
    if len(self.data)>0:
      for i in range(10):
        _data_to_add=_data_to_add.replace("__idx__",str(index))

      xmp="<?xpacket begin='' id=''?><x:xmpmeta xmlns:x='adobe:ns:meta/'><rdf:RDF xmlns:rdf='http://www.w3.org/1999/02/22-rdf-syntax-ns#'><rdf:Description rdf:mint='"\
          +str(base64.b64encode(bytes(_data_to_add,"utf8")),"utf8")\
          +"' xmlns:dc='http://purl.org/dc/elements/1.1/'></rdf:Description></rdf:RDF></x:xmpmeta><?xpacket end='r'?>"
    else:
      xmp=""

    if self.text and self.text["text"] and "<svg" in self.text["text"]:
      f=open(filename,"w")
      f.writelines(self.text["text"])
      f.close()
    else:
      if self.image.format=="GIF" or self.image.format=="WEBP" :
        log("Enregistrement d'un fichier animé")
        frames = [f.convert("RGBA") for f in ImageSequence.Iterator(self.image)]
        self.image.close()
        if len(xmp)>0:
          frames[0].save(filename,append_images=frames[1:],save_all=True,xmp=bytes(xmp,"utf8"))
        else:
          frames[0].save(filename,append_images=frames[1:],save_all=True)

        if not filename.endswith("webp"):
          log("Les metadonnées ne peuvent pas être inséré diretement dans l'image")
          l_index=filename.rindex(".")
          xmp_filename=filename[:l_index]+".xmp"
          with open(xmp_filename,"w") as f:
            f.write(xmp)
      else:
        log("Enregistrement d'un fichier statique")
        if self.image.format=="JPEG" or self.image.format=="JPG":
          if len(xmp)>0:
            self.image.save(filename,xmp=bytes(xmp,"utf8"))
          else:
            self.image.save(filename)
        else:
          log("... au format WEBP")
          self.image.save(filename,quality=int(quality),method=6,lossless=(quality==100),save_all=True,xmp=bytes(xmp,"utf8"))




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

  def apply_filter(self, filter_name:str):
    filter_name=filter_name.lower()
    rc=[]
    for elt in self.elements:
      if elt.image:
        _filter=None
        if filter_name=="blur":_filter=ImageFilter.BLUR

        if _filter is None:
          if filter_name=="equalize":new_elt=Sticker(image=ImageOps.equalize(elt.image).copy())
          if filter_name=="grayscale":new_elt=Sticker(image=ImageOps.grayscale(elt.image).copy())
          if filter_name=="flip":new_elt=Sticker(image=ImageOps.flip(elt.image).copy())
          if filter_name=="mirror":new_elt=Sticker(image=ImageOps.mirror(elt.image).copy())
          if filter_name=="solarize":new_elt=Sticker(image=ImageOps.solarize(elt.image).copy())
          if filter_name=="posterize":new_elt=Sticker(image=ImageOps.posterize(elt.image,8).copy())
          if filter_name=="to_white":new_elt=Sticker(image=ImageEnhance.Brightness(elt.image).enhance(0.7))
          if filter_name=="to_black":new_elt=Sticker(image=ImageEnhance.Brightness(elt.image).enhance(0.3))
          if filter_name=="contrast":new_elt=Sticker(image=ImageEnhance.Contrast(elt.image).enhance(0.8))
          if filter_name=="posterize":new_elt=Sticker(image=ImageOps.posterize(elt.image).copy())

        else:
          new_elt=Sticker(image=elt.image.filter(_filter).copy())

        rc.append(new_elt.toBase64())

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

  def generate(self,dir="",limit=100,seed_generator=0,width=500,height=500,quality=100,ext="webp",data=""):
    if seed_generator>0:seed(seed_generator)
    if len(dir)>0 and not dir.endswith("/"):dir=dir+"/"
    rc=list()

    self.sort()

    histo=[]
    index=0
    log("Lancement de la génération de "+str(limit)+" images")
    while index<limit:
      collage=Sticker("collage",dimension=(width,height),ext=ext,data=data)

      name=[]
      log("Génération du NFT "+str(index)+"/"+str(limit))
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
          elt.open()

          collage.fusion(elt,1 if elt.text is None else width/elt.text["dimension"][0])
          if layer.unique: layer.remove(elt)

          elt.close()


      if not name in histo and index<limit:
        index=index+1

        histo.append(name)
        if len(dir)>0:
          filename=dir+self.name+"_"+str(index)+"."+collage.ext if not "__idx__" in self.name else dir+self.name.replace("__idx__",str(index))+"."+collage.ext
          rc.append(filename)
          if collage.ext.lower()=="gif":
            rc.append(filename.replace(".gif",".xmp"))
          collage.save(filename,quality,index)
        else:
          filename=collage.toStr()
          rc.append(filename)

        collage.close()
        collage.delete()

    return rc




  def get_layer(self, name) -> Layer:
    for l in self.layers:
      if l.name==name:return l
    return None



  def delete(self, name):
    for l in self.layers:
      if l.name==name:
        self.layers.remove(l)
