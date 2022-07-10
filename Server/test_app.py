from ArtEngine import convert_to_gif
from PrestaTools import PrestaTools
from app import get_operation, get_nfts_from_src

_operation=get_operation("Main_devnet")
_store_section=_operation["store"]
prestashop=PrestaTools(_store_section["prestashop"]["api_key"])

image="./temp/image.gif"
product=prestashop.add_product("produit test",15,"","ma description",1,properties={"firstname":"david","lastname":"coignet"})
#prestashop.set_product_quantity(product,10)


#buf_image=convert_to_gif(image,filename="image.gif")
#image=prestashop.add_image(product_id,"./temp/image.gif")

pass
