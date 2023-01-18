import os
import random
import pytest

from flaskr import log
from flaskr.ArtEngine import ArtEngine, Sticker, Layer
from flaskr.TokenForge import upload_on_platform
from tests.test_tools import TEMP_TEST_DIR,RESSOURCE_TEST_DIR

PLATFORM_LIST=["db-server-tokenforge","server","infura","nftstorage"] #manque "github-nfluentdev-tests"

IMAGES={
  "backgrounds":[
    "https://img.freepik.com/free-photo/beautiful-milky-way-night-sky_53876-139825.jpg?w=1380&t=st=1670608013~exp=1670608613~hmac=b2ad049cb167a88487d282bb40d8061d98944ba401899a4354a699a0ab30363b",
    "https://img.freepik.com/free-photo/white-painted-wall-texture-background_53876-138197.jpg?w=996&t=st=1670608081~exp=1670608681~hmac=bc86415196bd4579744e799023fabd34b84b083a2860d12478f8c902b66d457d",
    "https://img.freepik.com/free-photo/abstract-luxury-blur-dark-grey-black-gradient-used-as-background-studio-wall-display-your-products-plain-studio-background_1258-54444.jpg?w=996&t=st=1670608097~exp=1670608697~hmac=ea40188a966f6dc040fe9cd8ddfa1d753ba08bb36f0029047a5b3468861d936c",
    RESSOURCE_TEST_DIR+"/fond1.png",
    RESSOURCE_TEST_DIR+"fond2.png",
    RESSOURCE_TEST_DIR+"fond3.png",
    RESSOURCE_TEST_DIR+"fond4.png"
  ],
  "stickers":[
    "https://i.pinimg.com/originals/cc/e8/f0/cce8f09ba31ec4a4115afcecfc2971fd.png",
    "https://m.media-amazon.com/images/I/81GhJuX-uRL.png",
    "https://1000logos.net/wp-content/uploads/2016/10/Apple-Logo.png",
    "https://logos-marques.com/wp-content/uploads/2021/10/meta-logo-1.png",
    RESSOURCE_TEST_DIR+"motif1.png",
    RESSOURCE_TEST_DIR+"motif2.png",
    RESSOURCE_TEST_DIR+"motif3.png",
    RESSOURCE_TEST_DIR+"motif4.png"
  ],
  "animated":[
    "https://helpx.adobe.com/content/dam/help/en/photoshop/how-to/create-animated-gif/jcr_content/main-pars/image_4389415/create-animated-gif_3a-v2.gif",
    "https://media.tenor.com/mZomesilZwoAAAAC/skull-caveira.gif",
    "http://ekladata.com/1DHTBeW4E3CVFx-CfYpnqDt9Igs/z64disco-3.gif",
    "https://bestanimations.com/media/mirror-balls/1536370706pink-disco-ball-animation-6.gif"
  ],
  "svgs":[
    RESSOURCE_TEST_DIR+"svg1.svg",
    RESSOURCE_TEST_DIR+"svg2.svg"
  ]
}

@pytest.fixture()
def artEngine():
  return ArtEngine()


def _random(lst):
  index=random.randint(0,len(lst)-1)
  return lst[index]



def test_create_sticker(section="backgrounds"):
  sticker=Sticker(name="background",image=_random(IMAGES[section]))
  assert not sticker is None
  return sticker


def test_create_layer(name="background",images=IMAGES["backgrounds"]):
  layer=Layer(name=name)
  for img in images:
    layer.add(Sticker(image=img))

  assert layer.count()==len(images)
  return layer


def clear_directory(dir=TEMP_TEST_DIR):
  for filename in os.listdir(dir):
    os.remove(dir+"/"+filename)


def test_paste_images(im1=None,im2=None,output_filename="collage.webp"):
  im1=im1 or _random(IMAGES["backgrounds"])
  im2=im2 or _random(IMAGES["stickers"])
  if output_filename=="collage.webp": clear_directory()
  s1=Sticker(image=im1)
  s2=Sticker(image=im2)
  log("Collage de "+str(s2)+" sur "+str(s1))
  s1.fusion(s2,1)
  s1.save(TEMP_TEST_DIR+output_filename)
  return True


def test_paste_with_svg():
  test_paste_images(im2=_random(IMAGES["svgs"]))



def test_paste_multiple_format():
  clear_directory()
  for i in range(0,20):
    background=Sticker(image=_random(IMAGES["backgrounds"]))
    foreground=Sticker(image=_random(IMAGES["stickers"]+IMAGES["svgs"]))
    rc=test_paste_images(background.image,foreground.image,"output"+str(i)+".webp")
    assert rc




def test_generate_collection(w=500,h=500,limit=10,dir=TEMP_TEST_DIR,
                             data={"title":"NFT de test","description":"ceci est la description"},
                             sections=["backgrounds","stickers"],
                             target_platform="server",collection_name="collection_test",seed=0):
  clear_directory(dir)
  artEngine=ArtEngine(collection_name)
  for n in sections:
    layer=test_create_layer(n,images=IMAGES[n])
    artEngine.add(layer)
  rc=artEngine.generate(dir,limit,seed_generator=seed,width=w,height=h,data=data,target_platform=target_platform,export_metadata=True)
  assert not rc is None
  assert len(rc)==len(os.listdir(dir)),"Il manque des fichiers"
  return rc



def test_collection_with_animated():
  clear_directory(TEMP_TEST_DIR)
  test_generate_collection(sections=["animated","stickers"],limit=3,seed=1)
  test_generate_collection(sections=["backgrounds","animated","stickers"],limit=3)



def test_all_platform_with_image(platforms=PLATFORM_LIST):
  img=Sticker(image=IMAGES["stickers"][1])
  for platform in platforms:
    print("Test de la platform "+platform)
    rc=upload_on_platform(img.toBase64(),platform)
    assert len(rc["url"])>0
    assert len(rc["cid"])>0


def test_all_platform_with_json(platforms=PLATFORM_LIST):
  doc={"description":"ma description","title":"my title"}
  for platform in platforms:
    rc=upload_on_platform(doc,platform)
    assert len(rc["url"])>0
    assert len(rc["cid"])>0















