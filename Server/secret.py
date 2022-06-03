#APP_SECRET_KEY="hh4271"
APP_SECRET_KEY="hh4271"
CRYPT_KEY_FOR_NFT=""

#Initialisation de la base sur le serveur:
#ouverture du firewall : firewall-cmd --zone=public --add-port=27017/tcp
#docker rm -f f80db
#docker run -d --name f80db --restart=always -v /root/f80db:/data/db -p 27017:27017 -e  MONGO_INITDB_ROOT_USERNAME=root -e MONGO_INITDB_ROOT_PASSWORD=hh4271 mongo

MONGO_INITDB_ROOT_USERNAME="root"
MONGO_INITDB_ROOT_PASSWORD="hh4271"
MONGO_CLUSTER_CONNECTION_STRING= "mongodb+srv://Hhoareau:hh4271@cluster0.mr2j9.mongodb.net/?retryWrites=true&w=majority"

USERNAME="contact@nfluent.io"
PASSWORD="hh42714271!!"

GOOGLE_ACCOUNT="nfluent@calviontherock.iam.gserviceaccount.com"
GOOGLE_ACCESS_KEY="GOOG1EZCKSY76GLYNQRL2IYHTBJX3XYCOB3LJY6ZMGS7OZLZKNNVNCX75KODY"
GOOGLE_SECRET_KEY="bZw6LY6t2NwPyA6AmwSwlsDO6iIg7RfmnFeoDjVa"

GITHUB_TOKEN="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"
SALT='sel'
ENCRYPTION_KEY="nfluentkey"
