#APP_SECRET_KEY="hh4271"
APP_SECRET_KEY="hh4271"
CRYPT_KEY_FOR_NFT=""

STORJ_API_KEY="jwgbxe2zddyhr2icqwmoh4wcuaaa"
STORJ_SATTELITE_ADDR="12L9ZFwhzVpuEKMUNUqkaTLGzwY9G24tbiigLiXpmZWKwmcNDDs@eu1.storj.io:7777"
STORJ_PASSPHRASE="hh4271!!"
STORJ_SECRETKEY="jyeawbsgiqzc3cqq3ayr3oue5w2rdwzn5swm6zs2z3znpl64gshbs"
STORJ_ENDPOINT="https://gateway.storjshare.io"

MEGAUPLOAD_EMAIL="rv@f80.fr"
MEGAUPLOAD_PASSWORD="hh4271!!"

#Initialisation de la base sur le serveur:
#ouverture du firewall : firewall-cmd --zone=public --add-port=27017/tcp ou "ufw allow 27017/tcp" si on utilise ufw
#docker rm -f f80db
#docker run -d --name f80db --restart=always -v /root/f80db:/data/db -p 27017:27017 -e  MONGO_INITDB_ROOT_USERNAME=root -e MONGO_INITDB_ROOT_PASSWORD=hh4271 mongo

MONGO_INITDB_ROOT_USERNAME="root"
MONGO_INITDB_ROOT_PASSWORD="hh4271"

WEB3_PASSWORD="hh4271!!"
MONGO_CLUSTER_CONNECTION_STRING= "mongodb+srv://Hhoareau:rootpassword@cluster0.mr2j9.mongodb.net/?retryWrites=true&w=majority"
MONGO_CLOUD_CONNECTION_STRING= "mongodb+srv://Hhoareau:rootpassword@cluster0.mr2j9.mongodb.net/?retryWrites=true&w=majority"
MONGO_WEB3_CONNECTION_STRING="mongodb://root:rootpassword@provider.bdl.computer:32754/"
MONGO_SERVER_CONNECTION_STRING="mongodb://root:rootpassword@38.242.210.208:27017/"


USERNAME="contact@nfluent.io"
PASSWORD="hh42714271!!"
SECRET_JWT_KEY="hh4271"

#voir https://polygonscan.com/myapikey
POLYGON_SCAN_API_KEY="9DJA8NCHRQGYTM39UEP51DNM12JVF6XIRA"

SECRET_ACCESS_CODE="040271"
ADMIN_EMAIL="hhoareau@gmail.com"
ADMIN_PERMS=["admin"]

SECRETS_FILE="./secrets_access.pkl"

ELROND_PASSWORD="Hh42714280!!"

GOOGLE_ACCOUNT="nfluent@calviontherock.iam.gserviceaccount.com"
GOOGLE_ACCESS_KEY="GOOG1EZCKSY76GLYNQRL2IYHTBJX3XYCOB3LJY6ZMGS7OZLZKNNVNCX75KODY"
GOOGLE_SECRET_KEY="bZw6LY6t2NwPyA6AmwSwlsDO6iIg7RfmnFeoDjVa"

#Obtenir un token https://github.com/settings/applications/new ou https://github.com/settings/applications/2161205
GITHUB_CLIENT_ID="5efede032a49331cf372"
GITHUB_SECRET_ID="37e45ea6679fdd0c87623874da835c732872a71f"

#voir https://docs.github.com/fr/authentication/keeping-your-account-and-data-secure/creating-a-personal-access-token
#procédure : https://github.com/settings/tokens/new et accorder toutes les permissions du repo
#Accorder les permissions
#GITHUB_TOKEN="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"
#GITHUB_TOKEN="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" #obtenu sur https://github.com/settings/tokens?type=beta
GITHUB_TOKEN="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" #obtenu sur https://github.com/settings/tokens?type=beta

GITHUB_ACCOUNT="nfluentdev"
SALT='sel'
ENCRYPTION_KEY="nfluentkey"

PERMS={
  "BjW8USn6XpyCW5dg95bNKey5XZ6KWaTox1nPDFYr4fdc":{
    "alias":"MainWallet","email":"hhoareau@gmail.com",
    "perms":["*"]
  },
  "2r44aqyxcMdxoDNpN7cK4WUYkB14B9ScriDd5CXBTfcG":{
    "copy_from":"BjW8USn6XpyCW5dg95bNKey5XZ6KWaTox1nPDFYr4fdc"
  },
  "Ee2zEFPiNhs7ZxuRg7aA1J4qDFNM5yQWH4CtzP7tssAt":{
    "alias":"Paul","email":"paul.dudule@gmail.com",
    "perms":["admin","create"]
  },
  "CegbuL4ShMnmunp2v61aBcUfQw57KFbzTsVKDPgKJZc2":{
    "alias":"Thomas","email":"thomas@nfluent.io",
    "perms":["*"]
  },

  "DKS7of5db3NoYWyGLqzvqs3UaN1nPEannsZ8Mo85B7jk":{
    "alias":"ThomasDev","email":"thomas@nfluent.io",
    "perms":["*"]
  },

  "DJuJznMC8sgMEYAVcEWje5Ap3wNYkmv3nnRP3XLGyom6":{
    "alias":"NFluentDev","email":"dev@nfluent.io",
    "perms":["*"]
  },

  "anonymous":{
    "alias":"anonymous",
    "email":"",
    "perms":["reload"]
  }
}

ELROND_PASSWORD="hh4271!!"

UNSPLASH_SETTINGS={"key":"916605164fceffa92953a549dfe86da9b29fe6c882200c92d342dc1b3cdbc630","endpoint":"https://api.unsplash.com/"}
PIXABAY_SETTINGS={"key": "5489947-2039fe3621c0de1cbb91d08c6","endpoint":"https://pixabay.com/api/"}