
from PrestaTools import PrestaTools
from app import get_operation


_operation=get_operation("Main_devnet")
_store_section=_operation["store"]
prestashop=PrestaTools(_store_section["prestashop"]["api_key"])

image="./temp/image.gif"
#_i=prestashop.get_images()
#_c=prestashop.get_product_categories("18")
#_p=prestashop.get_products(42)

import xmltodict

# _d={"language":{"@id":1,"#text":"test"}}
# xml=xmltodict.unparse(_d,pretty=False)


_p=prestashop.add_product("produit_test",12,"symbol","description",1,True,{"test":"oui"},{"address":"paul"})
#
# ipfs=IPFS(IPFS_SERVER)
# res=ipfs.add(prestashop.desc_to_dict(_p["description"]))

#buf_image=convert_to_gif(image,filename="image.gif")
#image=prestashop.add_image(product_id,"./temp/image.gif")

pass
