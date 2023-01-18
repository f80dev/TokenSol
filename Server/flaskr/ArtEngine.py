import base64

import os
import re
from io import BytesIO
from json import loads, dumps
from os.path import exists
from random import random,seed

import ffmpeg

import numpy as np
import requests
import svglib.svglib
from PIL import Image, ImageSequence, ImageFilter, ImageOps,ImageEnhance
from PIL.ImageDraw import Draw
from PIL.ImageFont import truetype
from PIL.ImageOps import pad
from reportlab.graphics import renderPM
from svglib.svglib import svg2rlg

from flaskr.settings import TEMP_DIR
from flaskr.TokenForge import upload_on_platform
from flaskr.Tools import now, log, get_fonts, normalize, extract_image_from_string, convert_image_to_animated, \
  merge_animated_image, get_filename_from_content, save_svg


class Element():
  name:str=""
  attributes:dict=dict()

  def __init__(self,name="",ext="png"):
    self.name=name if len(name)>0 else now("hex")+str(random()*1000000)
    self.ext=ext

  def fusion(self,to_concat):
    pass

  def save(self,filename,quality=98):
    pass

  def transform(self,scale,translation):
    pass

  def toStr(self):
    pass

  def render_svg(self,dictionnary:dict={},dimension=(500,500)):
    pass

  def get_code(self):
    pass

  def is_animated(self):
    pass



class Sticker(Element):
  image:Image=None
  text:dict=None
  dimension=None

  def __init__(self,name="",image=None,
               dimension=None,text:str=None,x:int=None,y:int=None,
               fontstyle={"color":(0,0,0,255),"size":100,"name":"corbel.ttf"},
               ext=None,data=""):

    #voir https://pillow.readthedocs.io/en/stable/handbook/image-file-formats.html
    if ext is None:
      ext="webp"
      if type(image)==str and str(image).lower().endswith(".svg"): ext="svg"
    else:
      ext=ext.replace(";","").lower()
      if "jpeg" in ext:ext="jpg"
      if "web" in ext:ext="webp"

    super().__init__(name,ext)
    self.data=data
    self.attributes=dict()

    if not image is None:
      if type(image)==str:
        if ext=="svg":
          if image.startswith("http"):
            svg_code=str(requests.get(image).content,"utf8")
            self.text={"text":svg_code}

          if image.startswith("data:"):
            self.text={"text":str(base64.b64decode(image.split("base64,")[1]),"utf8")}

          if self.text is None:
            if not "/" in image:image=TEMP_DIR+image
            with open(image,"r") as file:
              content=file.readlines()
              self.text={"text":"\n".join(content)}

          self.text["dimension"]=self.extract_dimension_from_svg(self.text["text"])
          self.render_svg(with_picture=False,dimension=self.dimension)
          return


        if not image.startswith("http"):
          if "base64" in image:
            self.image=extract_image_from_string(image)
          else:
            self.image=Image.open(image)
        else:
          if "/api/images/" in image:
            filename=image.split("/api/images/")[1].split("?")[0]
            if exists(TEMP_DIR+filename):
              self.image=Image.open(TEMP_DIR+filename)
            else:
              r=requests.get(image)
              if r.status_code==200:
                self.image=Image.open(BytesIO(requests.get(image).content))
          else:
            self.image=Image.open(BytesIO(requests.get(image).content))

        if self.image and self.image.mode!="RGBA" and not self.is_animated():
          self.image=self.image.convert("RGBA")

      else:
        if type(image)==bytes:
          self.image=Image.open(BytesIO(image))
        else:
          self.image=image.copy()

      #TODO code ci-dessous ne fonctionne pas, à corriger
      # if self.image and self.image.format!="JPEG" and not self.is_animated():
      #   ech=1
      #   l=abs(self.image.width-self.image.height)
      #   if self.image.width>self.image.height:
      #     offset=(self.image.width-self.image.height)/2
      #     box=(offset,0,self.image.height+offset,self.image.height)
      #   if self.image.width<self.image.height:
      #     offset=(self.image.height-self.image.width)/2
      #     box=(0,offset,self.image.width,self.image.width+offset)
      #   if l>0: self.image=self.image.crop((box[0]*ech,box[1]*ech,box[2]*ech,box[3]*ech))

    if not dimension is None:     #accepte la syntaxe 800x800
      if type(dimension)==str:
        dimension=(int(dimension.split("x")[0]),int(dimension.split("x")[1]))


    if text:
      self.text={
        "text":text,
        "fontstyle":fontstyle,
        "dimension":dimension,
        "x":x,"y":y
      }

    if self.image and dimension is None:
      dimension=self.image.size

    self.dimension=dimension

    if not text and not image:
      self.image=Image.new("RGBA",dimension)


  def is_animated(self):
    if self.image.format is None: return False
    return (self.image.format=="WEBP" or self.image.format=="GIF") and self.image.is_animated



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


  def transform(self,scale,translation):
    if scale!=(1,1) or translation!=(0,0):
      if ((not "_is_animated" in self.image.__dict__ and not "is_animated" in self.image.__dict__) or not self.image.is_animated):
        offset=(translation[0]/self.image.width,translation[1]/self.image.height)
        pad(self.image,size=(self.image.width*scale[0],self.image.height*scale[1]),color=None,centering=(offset[0]+0.5,offset[1]+0.5))


  def extract_dimension_from_svg(self,svg_code:str) -> (int,int):
    if "width=" in svg_code and "height=" in svg_code:
      height=re.findall(r'\d+',svg_code.split("height=")[1])
      width=re.findall(r'\d+',svg_code.split("width=")[1])
      return (int(height[0]),int(width[0]))
    else:
      return (500,500)


  def render_svg(self,dictionnary:dict={},dimension=(500,500),with_picture=True,prefix_name="svg"):

    filename,svg_code=save_svg(svg_code=self.text["text"],dir=TEMP_DIR,dictionnary=dictionnary)

    self.text={"text":svg_code}

    if with_picture:
      svg=svg2rlg(TEMP_DIR+filename)
      s=renderPM.drawToString(svg,"GIF",dpi=72)
      image=extract_image_from_string(s).convert("RGBA")

      newImage = []
      for item in image.getdata():
        if item[:3] == (255, 255, 255):
          newImage.append((255, 255, 255, 0))
        else:
          newImage.append(item)

      image.putdata(newImage)
      self.image=image.convert("RGBA")
      self.text["dimension"]=(self.image.width,self.image.height)
    else:
      self.text["dimension"]=self.extract_dimension_from_svg(svg_code)

      self.image=filename

    return self.image


  def clear(self):
    if self.text :
      self.image=None

  def open(self):
    if not self.image is None:
      if type(self.image)==str:
        self.image=Image.open(TEMP_DIR+self.image)
      else:
        if self.image.readonly==0 and self.image.format:
          if self.image.filename!="":
            self.image=Image.open(self.image.filename)
          else:
            if self.image.fp:
              self.image.fp.open()


  def close(self):
    if self.image and self.image.format and self.image.filename!="":
      try:
        self.image.close()
      except:
        log("Image "+str(self)+" déjà close")


  def __str__(self):
    rc=self.name
    try:
      if self.image and self.image.filename:rc=rc+" ("+self.image.filename+")"
      #if self.text:rc=rc+" ("+self.text[:20]+")"
      if self.is_animated(): rc=rc+" ("+str(self.image.n_frames)+" frames)"
    except:
      pass
    return rc


  def __del__(self):
    self.close()


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

    try:
      image=self.image.copy()
    except:
      try:
        image=self.image.filename
      except:
        image=self.image

    text=self.text["text"] if type(self.text)==dict and "text" in self.text else self.text
    rc=Sticker(name=new_name,image=image,text=text,ext=self.ext,data=self.data,dimension=self.dimension)
    return rc


  def replace_color(self,old_color,new_color):
    if old_color.startswith("#"):old_color=(int(old_color[1:2],16),int(old_color[3:4],16),int(old_color[5:6],16))
    if new_color.startswith("#"):new_color=(int(new_color[1:2],16),int(new_color[3:4],16),int(new_color[5:6],16))

    data = np.array(self.image)
    red, green, blue, alpha = data.T
    replacement_area = (red == old_color[0]) & (blue == old_color[2]) & (green == old_color[1])
    data[..., :-1][replacement_area.T] = (new_color[0], new_color[2], new_color[1])

    return Image.fromarray(data,"RGBA")




  def toBase64(self,format="WEBP",factor=1,quality=98) -> str:
    buffered = BytesIO()
    if self.image is None and self.text is not None:
      self.render_text(factor)

    self.image.save(buffered, format=format,quality=quality)
    self.clear()
    return "data:image/"+format.lower()+";base64,"+str(base64.b64encode(buffered.getvalue()),"utf8")





  def fusion(self,to_concat:Element,factor:float=1,replacement_for_svg:dict={},prefix=""):
      #log("Fusion des propriétés")
      for k in to_concat.attributes.keys():
        if k!="file":
          if not k in self.attributes:self.attributes[k]=[]
          if not to_concat.attributes[k] in self.attributes[k]:
            self.attributes[k].append(to_concat.attributes[k])

      #log("Fusion de "+self.name+" avec "+to_concat.name)
      if to_concat.ext=="svg":
        if "<svg" in to_concat.text["text"]:
          log("Collage d'un SVG")
          src=to_concat.render_svg(replacement_for_svg,self.dimension)
        else:
          log("Collage d'un texte")
          src=to_concat.render_text(factor)

      if self.image and to_concat.image:
        if to_concat.is_animated():
          # if not self.is_animated():
          #   self.image=convert_image_to_animated(self.image,to_concat.image.n_frames,prefix)

          log("Collage d'une image animé "+str(to_concat)+" sur la base "+str(self))
          self.image=merge_animated_image(self.image,to_concat.image,prefix)
          to_concat.image.close()

        else:
          log("Collage d'une image fixe ...")
          if not self.is_animated():
            log("... sur la base fixe")
            to_concat_resize=to_concat.image.resize(self.image.size).convert("RGBA")
            self.image.alpha_composite(to_concat_resize)
          else:
            log("... sur une base animé")
            to_concat.image=convert_image_to_animated(to_concat.image,self.image.n_frames,prefix)

            self.image=merge_animated_image(self.image,to_concat.image,prefix)
            to_concat.image.close()


  def save_xmp_in_extra_file(self,_data,filename):
    log("Les metadonnées ne peuvent pas être inséré diretement dans l'image")
    l_index=filename.rindex(".")
    xmp_filename=filename[:l_index]+".xmp"
    with open(xmp_filename,"w") as f:
      f.write(_data)
    return True


  def save(self,filename,quality=98,index=0,force_xmp_file=False):
    #voir https://pillow.readthedocs.io/en/stable/handbook/image-file-formats.html#webp pour le Webp
    _data_to_add=self.data
    if len(self.data)>0:
      for i in range(10): #Jusqu'a 10 remplacements
        _data_to_add=_data_to_add.replace("_idx_",str(index))

      _data=loads(_data_to_add)
      if not "title" in _data:_data["title"]=""
      if not "description" in _data:_data["description"]=""

      #Ajout des attributs collecté depuis les elements
      if "description" in self.attributes: _data["description"]=_data["description"]+" ".join(self.attributes["description"])
      if "name" in self.attributes: _data["title"]=_data["title"]+" ".join(self.attributes["name"])
      if "links" in self.attributes: _data["files"]=_data["files"]+"\n".join(self.attributes["links"])
      for k in self.attributes.keys():
        if k!="name" and k!="description" and k!="links":
          _data["properties"]=_data["properties"]+"\n"+k+"="+" ".join(self.attributes[k])
      _data_to_add=dumps(_data)


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
      if force_xmp_file: self.save_xmp_in_extra_file(xmp,filename)

      if self.is_animated():
        log("Enregistrement d'un fichier animé "+str(self))
        frames = [f.convert("RGBA") for f in ImageSequence.Iterator(self.image)]
        self.image.close()
        if len(xmp)>0:
          frames[0].save(filename,append_images=frames[1:],save_all=True,xmp=bytes(xmp,"utf8"))
        else:
          frames[0].save(filename,append_images=frames[1:],save_all=True)

        if not filename.endswith("webp"):
          self.save_xmp_in_extra_file()
      else:
        log("Enregistrement d'un fichier statique "+str(self))

        if self.image.format=="JPEG" or self.image.format=="JPG":
          if len(xmp)>0:
            self.image.save(filename,xmp=bytes(xmp,"utf8"))
          else:
            self.image.save(filename)
        else:
          log("... au format WEBP")
          self.image.save(filename,quality=int(quality),method=6,lossless=(quality==100),save_all=True,xmp=bytes(xmp,"utf8"))



  def add_propertie_to_data(self, key, value):
    """
    Ajoute une propriété aux datas du fichier
    :param key:
    :param value:
    :return:
    """
    if self.data=="": self.data="{}"
    _d=loads(self.data) if type(self.data)==str else self.data
    _d[key]=value
    self.data=dumps(_d)



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
    self.elements:[Element]=[]
    self.name=name if len(name)>0 else str(now())
    self.unique=unique if type(unique)!=str else False
    self.indexed=indexed if type(indexed)!=str else False
    self.scale=(1,1)
    self.translation=(0,0)
    self.position=position
    if element:self.add(element)


  def find_element(self,name):
    for e in self.elements:
      if normalize(e.name).startswith(normalize(name)): return e
    return None

  def order(self) -> int:
    pass

  def remove(self,img:Element) -> bool:
    if not img in self.elements:return False
    pos=self.elements.index(img)
    del self.elements[pos]
    return True


  def add(self,elt:Element):
    if elt is None: return self
    if elt.name=="": elt.name=self.name+"-"+str(len(self.elements))
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

    return rc.clone()


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

  def count(self):
    return len(self.elements)


class ArtEngine:
  """
  Moteur de génération
  """
  layers=[]
  attributes=[]

  def __init__(self,name="collage"):
    self.name=name

  def register_fonts(self,filter=""):
    log("Enregistrement des polices")
    for font in get_fonts():
      if filter=="" or font["name"]==filter:
        log("Enregistrement de "+font["name"])
        svglib.fonts.register_font(font["name"],"./Fonts/"+font["file"])

    log("Enregistrement terminé")
    return True


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
    if layer is None: return False
    layer.add(Sticker("",image))
    return True



  def sort(self):
    self.layers=sorted(self.layers,key=lambda x:x.position)



  def generate(self,dir="",
               limit=100,seed_generator=0,width=500,height=500,
               quality=100,ext="webp",data="",
               replacements={},
               attributes=list(),
               prefix="generate_",
               target_platform="",export_metadata=False
               ):
    """
    Génération des collections
    :param dir:
    :param limit:
    :param seed_generator:
    :param width:
    :param height:
    :param quality:
    :param ext:
    :param data:
    :param replacements:
    :return:
    """
    if seed_generator>0:seed(seed_generator)
    if len(dir)>0 and not dir.endswith("/"):dir=dir+"/"
    rc=list()

    self.sort()
    self.attributes=attributes

    histo=[]
    index=0

    log("Association des attributes")
    if "file" in attributes:
      self.associate_attributes()

    log("Lancement de la génération de "+str(limit)+" images")
    _try=0
    while index<limit and _try<20:
      collage=Sticker("collage",dimension=(width,height),ext=ext,data=data)

      name=[]
      log("\nGénération du NFT "+str(index+1)+"/"+str(limit))
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

          elt.transform(layer.scale,layer.translation)
          log("Collage de "+str(elt)+" sur "+str(collage))
          collage.fusion(elt,width/(1 if elt.text is None or elt.text["dimension"] is None else elt.text["dimension"][0]),replacements,prefix=prefix)
          if layer.unique:
            layer.remove(elt)

          elt.close()


      if not name in histo:
        if index<limit:
          index=index+1

          histo.append(name)
          if len(dir)>0:
            filename=dir+self.name+"_"+str(index)+"."+collage.ext if not "_idx_" in self.name else dir+self.name.replace("_idx_",str(index))+"."+collage.ext
            rc.append(filename)
            if collage.ext.lower()=="gif" or export_metadata:
              rc.append(filename+".xmp")

            if len(target_platform)>0:
              log("Upload de du résultat sur "+target_platform)
              result=upload_on_platform({"content":collage.toBase64(),"type":"image/webp"},target_platform)
              collage.add_propertie_to_data("storage",result["url"])

            collage.save(filename,quality,index,force_xmp_file=export_metadata)
          else:
            filename=collage.toStr()
            rc.append(filename)

          collage.close()
      else:
        _try=_try+1

    return rc




  def get_layer(self, name) -> Layer:
    for l in self.layers:
      if l.name==name:return l
    return None



  def delete(self, name):
    filter(lambda l:l.name!=name,self.layers)


  def associate_attributes(self):
    for layer in self.layers:
      for attribute in self.attributes:
        e=layer.find_element(attribute["file"])
        if e:
          pos=layer.elements.index(e)
          layer.elements[pos].attributes=attribute

    return True
