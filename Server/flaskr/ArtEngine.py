import base64
import hashlib
import json

import os
import re
from io import BytesIO
from json import loads, dumps
from os.path import exists
from random import random,seed
from time import sleep

import ffmpeg

import numpy as np
import requests
from PIL import Image, ImageSequence, ImageFilter, ImageOps,ImageEnhance
from PIL.ImageDraw import Draw
from PIL.ImageFont import truetype
from PIL.ImageOps import pad
from reportlab.graphics import renderPM
from svglib.svglib import svg2rlg

from flaskr.TokenForge import upload_on_platform
from flaskr.Tools import now, log, get_fonts, normalize, extract_image_from_string, convert_image_to_animated, \
  merge_animated_image, save_svg, extract_extension


class Element():
  name:str=""
  attributes:dict=dict()

  def __init__(self,name="",ext="png"):
    self.name=name if len(name)>0 else "elt_"+now("rand")
    self.ext=ext

  def fusion(self,to_concat):
    pass

  def save(self,filename,quality=98):
    pass

  def transform(self,scale,translation):
    pass

  def toStr(self):
    pass

  def get_code(self):
    pass

  def is_animated(self):
    pass



class Sticker(Element):
  image:Image=None
  text:dict=None
  ext:str=None
  file:str=None
  dimension=None
  work_dir="./temp/"

  def __init__(self,name="",image=None,
               dimension=None,text:str=None,x:int=None,y:int=None,
               fontstyle={"color":(0,0,0,255),"size":100,"name":"corbel.ttf"},
               ext=None,data="",work_dir="./temp/"):

    self.work_dir=work_dir
    if not exists(work_dir): raise RuntimeError("Répertoire de travail inexistant")

    #voir https://pillow.readthedocs.io/en/stable/handbook/image-file-formats.html
    super().__init__(name,ext)
    self.ext=self.get_ext(ext,image)
    self.data=data
    self.attributes=dict()

    if not image is None:
      if type(image)==str:
        image=image.replace(self.work_dir,"")
        # if image.startswith("./") and not image.startswith(self.work_dir):
        #   raise RuntimeError("Le repertoire de travail doit macher avec les fichiers contenant un chemin")
        self.file=image
        if not self.open():
          raise RuntimeError(self.file+" introuvable ou non compatible")
      else:
        if type(image)==bytes:
          self.image=Image.open(BytesIO(image))
        else:
          self.image=image.copy()


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



  def is_transparent(self):
    if self.image.info.get("transparency", None) is not None:
      return True
    if self.image.mode == "P":
      transparent = self.image.info.get("transparency", -1)
      for _, index in self.image.getcolors():
        if index == transparent:
          return True
    elif self.image.mode == "RGBA":
      extrema = self.image.getextrema()
      if extrema[3][0] < 255:
        return True

    return False



  def get_ext(self,ext:str,image:str) -> str:
    if ext is None:
      ext="webp"
      if type(image)==str:
        if image.endswith(".svg"): return "svg"
        if image.startswith("data:image/"):
          ext=image.split(";base64")[0][11:]
        else:
          if image.startswith("http"):
            ext=Image.open(BytesIO(requests.get(image).content)).format.lower()
          else:
            ext=image[image.rindex(".")+1:]
    else:
      ext=ext.replace(";","").lower()

    if "jpeg" in ext:ext="jpg"

    return ext



  def init_svg(self,image) -> bool:
    if type(image)==str:
      if image.startswith("http"):
        svg_code=str(requests.get(image).content,"utf8")
      else:
        if image.startswith("./"):
          if exists(self.work_dir+image): image=self.work_dir+image
          svg_code=open(image,"r").read()
        else:
          if exists(self.work_dir+image):
            svg_code=open(self.work_dir+image,"r").read()
          else:
            svg_code=image

      self.text={"text":svg_code}

      if image.startswith("data:"):
        self.text={"text":str(base64.b64decode(image.split("base64,")[1]),"utf8")}

    if self.text is None:
      if not "/" in image:image=self.work_dir+image
      with open(image,"r") as file:
        content=file.readlines()
        self.text={"text":"\n".join(content)}

    self.text["dimension"]=self.extract_dimension_from_svg(self.text["text"])
    self.render_svg(with_picture=True)
    return True

  def is_animated(self):
    if self.image is None or self.image.format is None: return False
    try:
      if self.image.is_animated: return True
    except:
      return False
    return (self.image.format=="WEBP" or self.image.format=="GIF") and self.image.is_animated


  def to_square(self,can_strech=True,extend=False):
    """
    Faire un crop carré
    :param can_strech:
    :return:
    """
    if self.image and not self.is_animated():
      if self.image.width==self.image.height:return False
      width, height = self.image.size
      if can_strech:#On procède à un léger ajustement
        new_size=(width if width>height else int(width*1.1),height if height>width else int(height*1.1))
        self.image.resize(new_size)
        width, height = self.image.size

      new_dimension=max(width, height) if extend else min(width, height)
      left = (width - new_dimension)/2
      top = (height - new_dimension)/2
      right = (width + new_dimension)/2
      bottom = (height + new_dimension)/2

      # Crop the center of the image
      self.image = self.image.crop((left, top, right, bottom))
      return True


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


  def transform(self,scale,translation,margin):
    if type(scale)==str: scale=[int(x) for x in scale.split(",")]
    if type(translation)==str: translation=[int(x) for x in translation.split(",")]
    if type(margin)==str: margin=[int(x) for x in margin.split(",")]
    if scale!=[1,1] or translation!=[0,0]:
      if ((not "_is_animated" in self.image.__dict__ and not "is_animated" in self.image.__dict__) or not self.image.is_animated):
        offset=(int(translation[0])/self.image.width,int(translation[1])/self.image.height)
        pad(self.image,size=(self.image.width*int(scale[0]),self.image.height*int(scale[1])),color=None,centering=(int(offset[0])+0.5,int(offset[1])+0.5))

    if margin!=[0,0] and self.is_transparent():
      self.image = self.image.crop((-margin[0], -margin[1], self.image.width+margin[0], self.image.height+margin[1]))


  def extract_dimension_from_svg(self,svg_code:str) -> (int,int):
    if "width=" in svg_code and "height=" in svg_code:
      height=re.findall(r'\d+',svg_code.split("height=")[1])
      width=re.findall(r'\d+',svg_code.split("width=")[1])
      return (int(height[0]),int(width[0]))
    else:
      return (500,500)


  def render_svg(self,dictionnary:dict={},with_picture=True,format="PNG") -> Image:

    filename,svg_code=save_svg(svg_code=self.text["text"],dir=self.work_dir,dictionnary=dictionnary)

    self.text={"text":svg_code}

    if with_picture:
      png_filename=self.work_dir+"temp_"+filename.replace(".svg","."+format)
      if exists(png_filename):
        image=Image.open(png_filename)
        self.image=image.copy()
        image.close()
      else:
        log("Rendering d'un SVG "+filename)
        svg=svg2rlg(self.work_dir+filename)
        s=renderPM.drawToString(svg,fmt=format,dpi=72)

        image=Image.open(BytesIO(s),formats=[format]).convert("RGBA")
        arr = np.array(image)
        mask = (arr[:, :, 0] == 255) & (arr[:, :, 1] == 255) & (arr[:, :, 2] == 255)
        arr[:, :, 3][mask] = 0
        self.image=Image.fromarray(arr, mode='RGBA')
        self.image.save(png_filename)

      self.text["dimension"]=(self.image.width,self.image.height)
    else:
      self.text["dimension"]=self.extract_dimension_from_svg(svg_code)
      self.image=filename

    return self.image.copy()


  def clear(self):
    if self.text :
      self.image=None

  def open(self) -> bool:
    if self.ext=="svg":
      self.init_svg(self.file)
      return True

    if not self.file.startswith("http"):
      if "base64" in self.file:
        self.image=extract_image_from_string(self.file)
      else:
        if not "/" in self.file: self.file=self.work_dir+self.file
        if not exists(self.file): return False
        self.image=Image.open(self.file)
    else:
      if "/api/images/" in self.file:
        filename=self.file.split("/api/images/")[1].split("?")[0]
        if exists(self.work_dir+filename):
          self.image=Image.open(self.work_dir+filename)
        else:
          r=requests.get(self.file)
          if r.status_code==200:
            self.image=Image.open(BytesIO(requests.get(self.file).content))
      else:
        req=requests.get(self.file,timeout=10000)
        if req.status_code==200:
          content=req.content
          if "<svg" in str(content):
            self.init_svg(str(content,"utf8"))
          else:
            self.image=Image.open(BytesIO(content))
        else:
          return False

    return True


    if self.image and self.image.mode!="RGBA" and not self.is_animated():
      self.image=self.image.convert("RGBA")

    if not self.image is None:
        if type(self.image)==str:
          self.image=Image.open(self.image)
        else:
          if self.image.readonly==0 and self.image.format:
            if self.image.filename!="":
              self.image=Image.open(self.image.filename)
            else:
              if self.image.fp:
                self.image.fp.open()
              else:
                return False

    return True


  def close(self):
    try:
      if self.image and self.image.format:
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
    if "/" in new_name:new_name=new_name[new_name.rindex("/")+1:]
    if new_name=="": new_name=self.name+"_clone."+self.ext
    if not new_name.endswith("."+self.ext):new_name=new_name+"."+self.ext

    self.save(self.work_dir+new_name)
    elt=Sticker(image=new_name,work_dir=self.work_dir,ext=self.ext)
    return elt

    # else:
    #   image=self.image.copy()
    #
    # text=self.text["text"] if type(self.text)==dict and "text" in self.text else self.text
    # rc=Sticker(name=new_name,image=image,text=text,ext=self.ext,data=self.data,dimension=self.dimension,work_dir=self.work_dir)
    # return rc


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
    if self.image is None and self.text is not None:  self.render_text(factor)

    self.save(buffered,quality)
    self.clear()
    return "data:image/"+format.lower()+";base64,"+str(base64.b64encode(buffered.getvalue()),"utf8")





  def fusion(self,to_concat:Element,factor:float=1,replacement_for_svg:dict={},prefix=""):
      #log("Fusion des propriétés")
      for k in to_concat.attributes.keys():
        if k!="file":
          if not k in self.attributes:self.attributes[k]=[]
          if not to_concat.attributes[k] in self.attributes[k]:
            self.attributes[k].append(to_concat.attributes[k])

      if to_concat.text:
        if "<svg" in to_concat.text["text"]:
          log("Collage d'un SVG")
          src=to_concat.render_svg(replacement_for_svg,self.dimension)
        else:
          log("Collage d'un texte")
          src=to_concat.render_text(factor)


      if self.image and to_concat.image:
        if to_concat.is_animated():
          #if not self.is_animated(): self.image=convert_image_to_animated(self.image,to_concat.image.n_frames,prefix,temp_dir=self.work_dir)

          log("Collage d'une image animé "+str(to_concat)+" sur la base "+str(self))
          self.image=merge_animated_image(self.image,to_concat.image,prefix,temp_dir=self.work_dir)
          if self.ext=="svg":
            self.text=""                      #Maintenant l'image n'est plus un SVG
            self.ext=self.image.format
          to_concat.image.close()
        else:
          to_concat.to_square(can_strech=True,extend=to_concat.is_transparent())
          log("Collage d'une image fixe ...")
          if not self.is_animated():
            log("... sur une base fixe")
            to_concat_resize=to_concat.image.resize(self.image.size).convert("RGBA")
            if self.image.mode=="RGB": self.image=self.image.convert("RGBA")
            self.image.alpha_composite(to_concat_resize)
          else:
            log("... sur une base animé")
            #to_concat.image=convert_image_to_animated(to_concat.image,self.image.n_frames,prefix,temp_dir=self.work_dir)

            self.image=merge_animated_image(self.image,to_concat.image,prefix,temp_dir=self.work_dir)
            to_concat.image.close()


  def save_xmp_in_extra_file(self,_data,filename):
    log("Les metadonnées ne peuvent pas être inséré diretement dans l'image. On les place dans "+filename)
    if not ".xmp" in filename:
      l_index=filename.rindex(".")
      filename=filename[:l_index]+".xmp"

    with open(filename,"w") as f:
      f.write(_data)
    return True


  def convert_data_to_xmp(self,data:dict,attributes:dict,index=0):
    _data_to_add=data
    if len(data)>0:
      for i in range(10): #Jusqu'a 10 remplacements
        _data_to_add=_data_to_add.replace("__idx__",str(index))

      _data=loads(_data_to_add)
      if not "title" in _data:_data["title"]=""
      if not "description" in _data:_data["description"]=""

      #Ajout des attributs collecté depuis les elements
      if "description" in attributes: _data["description"]=_data["description"]+" ".join(attributes["description"])
      if "name" in attributes: _data["title"]=_data["title"]+" ".join(attributes["name"])
      if "links" in attributes: _data["files"]=_data["files"]+"\n".join(attributes["links"])
      for k in attributes.keys():
        if k!="name" and k!="description" and k!="links":
          _data["properties"]=_data["properties"]+"\n"+k+"="+" ".join(attributes[k])
      _data_to_add=dumps(_data)

      xmp="<?xpacket begin='' id=''?><x:xmpmeta xmlns:x='adobe:ns:meta/'><rdf:RDF xmlns:rdf='http://www.w3.org/1999/02/22-rdf-syntax-ns#'><rdf:Description rdf:mint='" \
          +str(base64.b64encode(bytes(_data_to_add,"utf8")),"utf8") \
          +"' xmlns:dc='http://purl.org/dc/elements/1.1/'></rdf:Description></rdf:RDF></x:xmpmeta><?xpacket end='r'?>"
    else:
      xmp=""
    return xmp


  def save(self,filename="",quality=98,index=0,force_xmp_file=False):
    #voir https://pillow.readthedocs.io/en/stable/handbook/image-file-formats.html#webp pour le Webp
    if type(filename)==str and len(filename)==0: filename=self.get_filename()

    xmp=self.convert_data_to_xmp(self.data,self.attributes,index)
    if self.text and self.text["text"] and "<svg" in self.text["text"]:
      f=open(filename,"w") if type(filename)==str else filename
      f.writelines(self.text["text"])
      f.close()
    else:
      if force_xmp_file and type(filename)==str: self.save_xmp_in_extra_file(xmp,filename)

      if self.is_animated():
        log("Enregistrement d'un fichier animé "+str(self))
        if len(xmp)>0:
          if self.image.format!="WEBP":
            xmp_filename=filename if type(filename)==str else self.work_dir+self.name+"_"+str(index)
            self.save_xmp_in_extra_file(xmp,xmp_filename+".xmp")
            self.image.save(filename,format=self.image.format,save_all=True,disposal=2)
          else:
            self.image.save(filename,format=self.image.format,save_all=True,xmp=bytes(xmp,"utf8"),disposal=2)
        else:
          self.image.save(filename,format=self.image.format,save_all=True,disposal=2)



      else:
        log("Enregistrement d'un fichier statique "+str(self))

        if self.image.format=="JPEG" or self.image.format=="JPG":
          if len(xmp)>0:
            self.image.save(filename,xmp=bytes(xmp,"utf8"))
          else:
            self.image.save(filename,format=self.image.format)
        else:
          log("... au format WEBP")
          self.image.save(filename,quality=int(quality),
                          method=6,lossless=(quality==100),
                          save_all=True,format="webp",
                          xmp=bytes(xmp,"utf8"))
          if type(filename)==str:
            self.image.close()



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

  def get_filename(self,prefix="temp",format="webp"):
    rc=prefix+"_"+hashlib.sha256(self.image.tobytes()+bytes(self.data,"utf8")).hexdigest()+"."+format
    return rc


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
  def __init__(self,name="",elements=[],position=0,unique=False,indexed=True,scale="1,1",
               translation="0,0",margin="0,0",work_dir="./temp",object=None):

    if object:
      for k, v in object.items():
        setattr(self, k, v)
    else:
      self.name=name if len(name)>0 else "layer_"+now("hex")
      self.unique=unique if type(unique)!=str else False
      self.indexed=indexed if type(indexed)!=str else False
      self.scale=[float(x) for x in scale.split(",")]
      self.translation=[float(x) for x in translation.split(",")]
      self.margin=[float(x) for x in margin.split(",")]
      self.position=position
      self.work_dir=work_dir

    self.elements:[Element]=[]
    for element in elements:
      e=Sticker(name=element["name"] if "name" in element else "name_"+now("rand"),
                ext=element["ext"] if "ext" in element else extract_extension(element["image"]),
                image=element["image"]
                )
      self.add(e)


  def find_element(self,name) -> Sticker:
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
    rc:Sticker=None
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
          if filter_name=="equalize":new_image=ImageOps.equalize(elt.image).copy()
          if filter_name=="grayscale":new_image=ImageOps.grayscale(elt.image).copy()
          if filter_name=="flip":new_image=ImageOps.flip(elt.image).copy()
          if filter_name=="mirror":new_image=ImageOps.mirror(elt.image).copy()
          if filter_name=="solarize":new_image=ImageOps.solarize(elt.image).copy()
          if filter_name=="posterize":new_image=ImageOps.posterize(elt.image,8).copy()
          if filter_name=="to_white":new_image=ImageEnhance.Brightness(elt.image).enhance(0.7)
          if filter_name=="to_black":new_image=ImageEnhance.Brightness(elt.image).enhance(0.3)
          if filter_name=="contrast":new_image=ImageEnhance.Contrast(elt.image).enhance(0.8)
          if filter_name=="posterize":new_image=ImageOps.posterize(elt.image).copy()

        else:
          new_image=elt.image.filter(_filter).copy()

        new_elt=Sticker(image=new_image,work_dir=self.work_dir)
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
  work_dir="./temp/"
  domain_appli=""

  def __init__(self,name="collage",work_dir="./temp",domain_appli="https://nfluent.io",layers=[],config:dict=None):
    self.name=name
    self.work_dir=work_dir
    self.domain_appli=domain_appli
    self.layers=[]
    if not config is None:
      self.name=config["name"]
      layers=config["layers"]
    for l in layers:
      self.add(Layer(name=l["name"],unique=l["unique"],indexed=l["indexed"],
                     translation=l["translation"],position=l["position"],
                     elements=l["elements"]))


  def reset(self):
    self.layers.clear()

  def add(self,layer,position=-1):
    l=self.get_layer(layer.name)
    if l is None:
      if position==-1:
        self.layers.append(layer)
      else:
        self.layers.insert(position,layer)
    else:
      pos=self.layers.index(l)
      self.layers[pos]=layer


  def add_image_to_layer(self,name,image):
    layer=self.get_layer(name)
    if layer is None: return False

    if type(image)!=Sticker:
      image=Sticker("photo"+now("rand"),image,work_dir=self.work_dir)
    layer.add(image)

    return True



  def sort(self):
    self.layers=sorted(self.layers,key=lambda x:x.position)


  def generate_sequences(self,limit=200,_seed=0) -> list :
    log("Génération des combinatoires")
    _try=0
    sequences=[]
    seed(_seed)
    while len(sequences)<limit and _try<200:
      seq=[]
      for layer in self.layers:
        elt:Sticker=None if len(layer.elements)==0 else (layer.random() if not layer.unique else layer.elements[0])
        if elt:
          seq.append({"layer":layer.name,"sticker":elt.name})
          if layer.unique:
            layer.remove(elt)

      if not seq in sequences and len(seq)==len(self.layers):
        sequences.append(seq)
      else:
        _try=_try+1

    return sequences


  def compose(self,items:list,width=400,height=400,ext="webp",data={},replacements={},prefix="generate_",) -> Sticker:
    """
    fusion des premiers elements d'un ensemble de couche
    :param layers:
    :param width:
    :param height:
    :param ext:
    :param data:
    :return:
    """
    if type(data)==dict: data=json.dumps(data)
    for k in replacements.keys():
      data=data.replace(k,replacements[k])
    collage=Sticker("collage",dimension=(width,height),ext=ext,data=data,work_dir=self.work_dir)
    for item in items:
      layer=self.get_layer(item["layer"])
      elt=layer.find_element(item["sticker"])
      elt.open()
      elt.transform(layer.scale,layer.translation,layer.margin)
      log("Collage de "+str(elt)+" sur "+str(collage))
      collage.fusion(elt,width/(1 if elt.text is None or elt.text["dimension"] is None else elt.text["dimension"][0]),replacements,prefix=prefix)
      elt.close()

    return collage




  def generate(self,dir="",
               limit=100,seed_generator=0,width=500,height=500,
               quality=100,ext="webp",data="",
               attributes=list(),
               target_platform="",
               export_metadata=False,
               domain_server="",
               sequences=[]
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
    if type(data)==dict:data=json.dumps(data)
    if seed_generator>0:seed(seed_generator)
    if len(dir)>0 and not dir.endswith("/"):dir=dir+"/"
    rc=list()

    self.sort()
    self.attributes=attributes

    index=0

    log("Association des attributes")
    if "file" in attributes:
      self.associate_attributes()


    for seq in sequences:
      collage=Sticker("collage",dimension=(width,height),ext=ext,data=data,work_dir=self.work_dir)

      name=[]
      log("\nGénération du NFT "+str(index+1)+"/"+str(limit))

      for idx_layer,elt in enumerate(seq):
          self.compose(seq,width,height,ext,data)

      if index<limit:
        index=index+1

        if len(dir)>0:
          prefix=""
          filename=dir+prefix+self.name+"_"+str(index)+"."+collage.ext if not "_idx_" in self.name else dir+self.name.replace("_idx_",str(index))+"."+collage.ext
          rc.append(filename)
          if collage.ext.lower()=="gif" or export_metadata:
            rc.append(filename+".xmp")

          if len(target_platform)>0 and target_platform!="preview":
            log("Upload du résultat sur "+target_platform)
            result=upload_on_platform({"content":collage.toBase64(),"type":"image/webp"},target_platform,domain_server=domain_server,upload_dir=dir)
            if result is None:
              raise RuntimeError("Impossible de charger les visuels sur la plateforme de stockage")
            collage.add_propertie_to_data("storage",result["url"])

          collage.save(filename,quality,index,force_xmp_file=export_metadata)
        else:
          filename=collage.toStr()
          rc.append(filename)

        collage.close()

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
