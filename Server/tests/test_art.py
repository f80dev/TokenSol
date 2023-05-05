import os
import random
import time
from os.path import exists

import pytest
from PIL import Image, ImageSequence

from flaskr import log
from flaskr.ArtEngine import ArtEngine, Sticker, Layer
from flaskr.TokenForge import upload_on_platform
from flaskr.Tools import generate_svg_from_fields,  register_fonts
from tests.test_tools import TEMP_TEST_DIR,RESSOURCE_TEST_DIR

PLATFORM_LIST=["github-nfluentdev-storage-main","db-server-tokenforge","server","infura","nftstorage"] #manque ""

IMAGES={
  "backgrounds":[
    "https://img.freepik.com/free-photo/beautiful-milky-way-night-sky_53876-139825.jpg?w=1380&t=st=1670608013~exp=1670608613~hmac=b2ad049cb167a88487d282bb40d8061d98944ba401899a4354a699a0ab30363b",
    "https://img.freepik.com/free-photo/white-painted-wall-texture-background_53876-138197.jpg?w=996&t=st=1670608081~exp=1670608681~hmac=bc86415196bd4579744e799023fabd34b84b083a2860d12478f8c902b66d457d",
    "https://img.freepik.com/free-photo/abstract-luxury-blur-dark-grey-black-gradient-used-as-background-studio-wall-display-your-products-plain-studio-background_1258-54444.jpg?w=996&t=st=1670608097~exp=1670608697~hmac=ea40188a966f6dc040fe9cd8ddfa1d753ba08bb36f0029047a5b3468861d936c",
    RESSOURCE_TEST_DIR+"fond1.png",
    RESSOURCE_TEST_DIR+"fond2.png",
    RESSOURCE_TEST_DIR+"fond3.png",
    RESSOURCE_TEST_DIR+"fond4.png"
  ],
  "stickers":[
    "https://i.pinimg.com/originals/cc/e8/f0/cce8f09ba31ec4a4115afcecfc2971fd.png",
    "https://m.media-amazon.com/images/I/81GhJuX-uRL.png",
    "https://1000logos.net/wp-content/uploads/2016/10/Apple-Logo.png",
    "https://logos-marques.com/wp-content/uploads/2021/10/meta-logo-1.png",
    "motif1.png",
    "motif2.png",
    "motif3.png",
    "motif4.png"
  ],
  "animated":[
    "dog.gif",
    "boule_facette.gif",
    "https://helpx.adobe.com/content/dam/help/en/photoshop/how-to/create-animated-gif/jcr_content/main-pars/image_4389415/create-animated-gif_3a-v2.gif",
    "https://media.tenor.com/mZomesilZwoAAAAC/skull-caveira.gif",
    "http://ekladata.com/1DHTBeW4E3CVFx-CfYpnqDt9Igs/z64disco-3.gif",
    "https://bestanimations.com/media/mirror-balls/1536370706pink-disco-ball-animation-6.gif",

  ],
  "svgs":[
    "svg1.svg",
    "svg2.svg",
    "voeux2023.svg"
  ]
}

@pytest.fixture()
def artEngine():
  return ArtEngine()


def _random(lst):
  index=random.randint(0,len(lst)-1)
  return lst[index]

def test_clone():
  for section in IMAGES.keys():
    clear_directory()
    image=get_image(section=section)

    log("Clonage de "+image)
    sticker=Sticker(image=image,work_dir=TEMP_TEST_DIR)
    assert not sticker.ext is None,"L'extensione est vide pour "+image

    clone=sticker.clone("myclone")
    assert clone.is_animated()==sticker.is_animated()
    clone.close()
    sticker.close()



def get_image(url:str=None,section=None,index=-1) -> str:
  if url is None:

    assert not section is None
    assert section in IMAGES,"la section "+section+" ne fait pas partie des images"
    if index==-1:
      url=_random(IMAGES[section])
    else:
      url=IMAGES[section][index]

  log("Utilisation de "+url)
  if url.startswith("http"):return url
  if "/" in url: return url

  return RESSOURCE_TEST_DIR+url


def test_sequence():
  clear_directory(TEMP_TEST_DIR)
  filename=get_image(section="animated",index=1)
  img=Image.open(filename,"r")
  img.save(TEMP_TEST_DIR+"/master.gif",save_all=True, disposal=2)
  #transfer_sequence_to_disk(img,dir=TEMP_TEST_DIR)



def test_paste_fixe_to_animated():
  clear_directory()
  url=test_paste_images(im1=get_image(section="svgs"),im2=get_image(section="animated"),output_filename="collage.gif")
  rc=Sticker(image=url,work_dir=TEMP_TEST_DIR)
  assert rc.is_animated,"Le résultat devrait être une image animée"



# def test_pillow_library():
#   image = get_image("lapin.")
#   frames = []
#
#   angle=0
#   for frame in ImageSequence.Iterator(image):
#     for i in range(30):
#       frame=frame.rotate(angle)
#       frames.append(frame.copy())
#       angle += 1
#
#   frames[0].save("./tests/lapin.webp", save_all=True, append_images=frames[1:],optimize=False,loop=0)


def test_load(section="animated"):
  for url in IMAGES[section]:
    log("Test de "+url)
    url=get_image(url)
    ext=url[url.rindex(".")+1:]
    if ext and len(ext)>0:
      sticker=Sticker(name="test",image=url,work_dir=TEMP_TEST_DIR)
      assert sticker.is_animated()
      assert sticker.image.is_animated
      assert sticker.image.format
      assert sticker.image.format.lower()==ext.lower()
      assert sticker.image.n_frames>1
  time.sleep(2)
  clear_directory()



def test_create_sticker(section="backgrounds",index=0):
  clear_directory()
  for index in range(len(IMAGES[section])):
    can_strech=(index % 2==0)
    sticker=Sticker(name="background",image=get_image(section=section,index=index),work_dir=TEMP_TEST_DIR)
    sticker.to_square(can_strech=can_strech,extend=sticker.is_transparent())
    assert not sticker is None
    assert not can_strech or abs(sticker.image.height-sticker.image.width)<10


def test_create_layer(name="backgrounds"):
  images=IMAGES[name]
  layer=Layer(name=name)

  for img in images:
    layer.add(Sticker(image=get_image(url=img),work_dir=TEMP_TEST_DIR))

  assert layer.count()==len(images)
  return layer


def clear_directory(dir=TEMP_TEST_DIR):
  for filename in os.listdir(dir):
    try:
      os.remove(dir+"/"+filename)
    except:
      time.sleep(4)
      os.remove(dir+"/"+filename)



def test_paste_images(im1=None,im2=None,output_filename="collage.webp"):
  im1=im1 or get_image(section="backgrounds")
  im2=im2 or get_image(section="stickers")
  s1=Sticker(image=im1,work_dir=TEMP_TEST_DIR)
  s2=Sticker(image=im2,work_dir=TEMP_TEST_DIR)
  log("Collage de "+str(s2)+" sur "+str(s1))
  s1.fusion(s2,factor=1)
  s1.save(TEMP_TEST_DIR+output_filename)
  s1.close()
  return TEMP_TEST_DIR+output_filename


def test_paste_with_svg():
  clear_directory()
  test_paste_images(im2=get_image(section="svgs"))


def test_paste_several_svg():
  clear_directory()
  rc=test_paste_images(im1=get_image(section="svgs"),im2=get_image(section="svgs"))
  assert exists(rc)



def test_clone_svg(clone_filename="copie de svg.svg"):
  clear_directory()
  rc=Sticker(image=get_image(section="svgs"),work_dir=TEMP_TEST_DIR)
  rc.clone(clone_filename)
  assert exists(TEMP_TEST_DIR+clone_filename)


def test_paste_svg_on_jpeg():
  clear_directory()
  background=Sticker(image=get_image(section="backgrounds",index=0),work_dir=TEMP_TEST_DIR)
  foreground=Sticker(image=get_image(section="svgs"),work_dir=TEMP_TEST_DIR)
  rc=test_paste_images(background.image,foreground.image,"output.webp")
  assert not rc is None,"Impossible de coller "+str(foreground)+" sur "+str(background)
  assert exists(rc)



def test_paste_multiple_format():
  clear_directory()
  for i in range(0,20):
    background=Sticker(image=get_image(section="backgrounds"),work_dir=TEMP_TEST_DIR)
    url=_random(IMAGES["stickers"]+IMAGES["svgs"])
    foreground=Sticker(image=get_image(url),work_dir=TEMP_TEST_DIR)
    rc=test_paste_images(background.image,foreground.image,"output"+str(i)+".webp")
    assert not rc is None,"Impossible de coller "+str(foreground)+" sur "+str(background)
    assert exists(rc)



def test_svg_treatment_1():
  clear_directory()
  foreground=Sticker(image=get_image(section="svgs"),work_dir=TEMP_TEST_DIR)
  rc:Image=foreground.render_svg()
  assert not rc is None
  rc.save(open(TEMP_TEST_DIR+"test.gif","wb"))


def test_load_svg_from_web():
  clear_directory()
  svg=Sticker(image="https://nfluent.io/assets/certificat_authenticite_black.svg",work_dir=TEMP_TEST_DIR)
  svg.render_svg(dictionnary={"title":"ceci est le titre"}).save(open(TEMP_TEST_DIR+"test.gif","wb"))
  assert not svg is None


def test_position_svg():
  clear_directory()
  svg=Sticker(image=RESSOURCE_TEST_DIR+"certificat_authenticite_black.svg",work_dir=TEMP_TEST_DIR)
  svg.render_svg(dictionnary={"title":"ceci est le titre"}).save(open(TEMP_TEST_DIR+"test.gif","wb"))
  assert not svg is None


def test_register_fonts():
  register_fonts(20)


def test_conversion_font_svg():
  clear_directory()
  artEngine:ArtEngine=ArtEngine()
  register_fonts(limit=5)
  svg=Sticker(image=RESSOURCE_TEST_DIR+"font_test.svg",work_dir=TEMP_TEST_DIR)
  svg.render_svg().save(open(TEMP_TEST_DIR+"test.gif","wb"))
  assert not svg is None




def test_svg_treatment_2():
  clear_directory()
  background=Sticker(image="https://images.unsplash.com/photo-1586075010923-2dd4570fb338?ixid=Mnw5OTUyN3wwfDF8c2VhcmNofDR8fHBhcGVyfGVufDB8fHx8MTY3OTA0ODczMA&ixlib=rb-4.0.3",work_dir=TEMP_TEST_DIR)
  background.image=background.image.convert("RGBA").crop((0,0,400,400))
  svg=Sticker(image="https://nfluent.io/assets/certificat_authenticite_black.svg",work_dir=TEMP_TEST_DIR)
  foreground=Sticker(image=svg.render_svg(dictionnary={"title":"ceci est le titre"}))
  background.fusion(foreground)
  background.save(open(TEMP_TEST_DIR+"test.gif","wb"))



def test_edit_serie():
  """
  permet de vérifier le bon fonctionnement du système de génération de série sur la base d'une suite de type a|b|c|d
  :return:
  """
  clear_directory()
  register_fonts()
  svg=Sticker(image=RESSOURCE_TEST_DIR+"access_card.svg")
  images=generate_svg_from_fields(svg.text["text"])
  for i,image in enumerate(images):
    svg=Sticker(text=image)
    svg.render_svg().save(open(TEMP_TEST_DIR+"test"+str(i)+".png","wb"))



def test_generate_collection(w=500,h=500,limit=5,dir=TEMP_TEST_DIR,
                             data={"title":"NFT de test","description":"ceci est la description"},
                             sections=["backgrounds","stickers"],
                             target_platform="server",collection_name="collection_test",seed=19):
  clear_directory(dir)
  random.seed(seed)
  artEngine=ArtEngine(collection_name,work_dir=dir)
  for section in sections:
    layer=test_create_layer(section)
    artEngine.add(layer)
  rc=artEngine.generate(dir,limit,seed_generator=seed,width=w,height=h,data=data,target_platform=target_platform,export_metadata=True)
  assert not rc is None
  return rc


def test_composition(dir=TEMP_TEST_DIR,sections=["backgrounds","stickers"],limit=4):
  clear_directory(dir)
  artEngine=ArtEngine("composition_test",work_dir=dir)
  for section in sections:
    layer=test_create_layer(section)
    artEngine.add(layer)

  seq=artEngine.generate_sequences(limit=limit)
  for idx,s in enumerate(seq):
    image=artEngine.compose(s)
    image.save(dir+"file_"+str(idx)+".webp")



def test_generate_with_xmp(w=500,h=500,dir=TEMP_TEST_DIR,
                             data={
                               "title":"NFT de test",
                               "description":"ceci est la description",
                               "tags":"birthday","royalties":1,
                               "files":"https://nfluent.io",
                               "marketplace":{"price":1,"quantity":2}
                              },
                             target_platform="nftstorage",collection_name="collection_test",seed=19):
  clear_directory(dir)
  random.seed(seed)
  artEngine=ArtEngine(collection_name,work_dir=TEMP_TEST_DIR)
  artEngine.add(Layer(name="fond").add(Sticker(image=get_image(section="backgrounds",index=4),work_dir=TEMP_TEST_DIR)))
  artEngine.add(Layer(name="sticker").add(Sticker(image=get_image(section="stickers",index=1),work_dir=TEMP_TEST_DIR)))
  rc=artEngine.generate(dir,1,seed_generator=seed,width=w,height=h,data=data,target_platform=target_platform,export_metadata=False)
  assert not rc is None
  return rc


def test_generate_svg():
  master=Sticker(image=get_image(section="svgs",index=2),work_dir=TEMP_TEST_DIR)
  images=generate_svg_from_fields(master.text["text"])
  assert not images is None


def test_collection_with_animated():
  clear_directory(TEMP_TEST_DIR)
  rc=test_generate_collection(sections=["animated","stickers"],limit=3,seed=1)
  rc=test_generate_collection(sections=["backgrounds","animated","stickers"],limit=3)



def test_all_platform_with_image(platforms=PLATFORM_LIST):
  img=Sticker(image=IMAGES["stickers"][1],work_dir=TEMP_TEST_DIR)
  for platform in platforms:
    print("Test de la platform "+platform)
    rc=upload_on_platform(img.toBase64(),platform,upload_dir=TEMP_TEST_DIR,domain_server="http://localhost:4200/")
    assert len(rc["cid"])>0


