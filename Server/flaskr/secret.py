#APP_SECRET_KEY="hh4271"
APP_SECRET_KEY="hh4271"
CRYPT_KEY_FOR_NFT=""

#Initialisation de la base sur le serveur:
#ouverture du firewall : firewall-cmd --zone=public --add-port=27017/tcp
#docker rm -f f80db
#docker run -d --name f80db --restart=always -v /root/f80db:/data/db -p 27017:27017 -e  MONGO_INITDB_ROOT_USERNAME=root -e MONGO_INITDB_ROOT_PASSWORD=hh4271 mongo

MONGO_INITDB_ROOT_USERNAME="root"
MONGO_INITDB_ROOT_PASSWORD="hh4271"
WEB3_PASSWORD="hh4271!!"
MONGO_CLUSTER_CONNECTION_STRING= "mongodb+srv://Hhoareau:hh4271@cluster0.mr2j9.mongodb.net/?retryWrites=true&w=majority"
MONGO_WEB3_CONNECTION_STRING="mongodb://root:rootpassword@provider.bdl.computer:32754/"

USERNAME="contact@nfluent.io"
PASSWORD="hh42714271!!"
SECRET_JWT_KEY="hh4271"

#voir https://polygonscan.com/myapikey
POLYGON_SCAN_API_KEY="9DJA8NCHRQGYTM39UEP51DNM12JVF6XIRA"

SECRET_ACCESS_CODE="42714280"

SECRETS_FILE="./secrets_access.pkl"

ELROND_PASSWORD="Hh42714280!!"

GOOGLE_ACCOUNT="nfluent@calviontherock.iam.gserviceaccount.com"
GOOGLE_ACCESS_KEY="GOOG1EZCKSY76GLYNQRL2IYHTBJX3XYCOB3LJY6ZMGS7OZLZKNNVNCX75KODY"
GOOGLE_SECRET_KEY="bZw6LY6t2NwPyA6AmwSwlsDO6iIg7RfmnFeoDjVa"

GITHUB_TOKEN="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"
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
