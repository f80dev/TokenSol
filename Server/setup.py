from setuptools import find_packages, setup

setup(
	name='flaskr',
	version='1.0.0',
	packages=find_packages(),
	include_package_data=True,
	install_requires=[
		'flask',"Flask-Cors","pyyaml","pyopenssl","solana","base58","ipfshttpclient","erdpy","secret-sdk",
		"pyqrcode","pillow","py7zr","ffmpeg-python","pypng","dnspython","pymongo","google-cloud-storage","PyGithub","fonttools",
		"numpy","svglib","pycairo","imageio","bip_utils","matplotlib","Unidecode","xmltodict","pypng","flask-jwt-extended","apscheduler","Flask-Caching","requests-cache","cryptography",
		"networkx","flask-socketio","eth-account","py-solc-x","web3"
	],
)



