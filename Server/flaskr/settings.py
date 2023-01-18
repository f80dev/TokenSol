ENCRYPT_KEY="hh040280!!"
NFT_STORAGE_KEY="eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJzdWIiOiJkaWQ6ZXRocjoweEQ4ZTk2MERCRDEwYjVlNTExMTU5REI5RDk3NzQ0MkI2ODI1OWU1MTQiLCJpc3MiOiJuZnQtc3RvcmFnZSIsImlhdCI6MTY0NTcyMzU4MDU0MSwibmFtZSI6Im5mbHVlbnQifQ.5rzoF_fn5iZJLY2nD-yTIt3RoxWKoOuh_rPZ-prwnds"

GITHUB={
	"user":"f80dev",
	"token":"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",
	"branch":"storage",
	"repository":"TokenSol"
}

#Le repertoire de travail est fixé sur Server, du coup les répertoires suivant commence par "." (vs "..")
TEMP_DIR="./temp/"
OPERATIONS_DIR="./Operations/"
CONFIG_DIR="./Configs/"
STATIC_FOLDER="./flaskr/static/"

IPFS_PORT=5001
#IPFS_SERVER="/ip4/75.119.159.46/tcp/"+str(IPFS_PORT)+"/http"   #
IPFS_SERVER="/ip4/173.249.41.158/tcp/"+str(IPFS_PORT)+"/http"   #

FTX_API_KEY="GN5PIvejHZ0h2BXDmXziybR5XW4fdSrzRFa0R2Fw"
FTX_API_SECRET="Rge4X3p8KtV3ZJvd0yQXSCqIRiWZDeLEXTLO6O_s"

INFURA_PROJECT_ID="28bvVmf3lmX8xWj3UlHCaNPD0lQ"
INFURA_PROJECT_SECRET="8e4ed073cf43c280787c3cf2e7c2176a"

SIGNATURE="L'équipe <a href='https://nfluent.io'>NFluenT</a>"
APPNAME="TokenForge"

SMTP_SERVER="ssl0.ovh.net"
SMTP_SERVER_PORT=587
IMAP_SERVER="imap.ionos.fr"

#Localisation de la base de donnée général du système, notamment pour les pool de mining
DBSERVER_SYSTEM="server"
DBNAME_SYSTEM="tokenforge"

MAIL_NEW_ACCOUNT="mail_new_account"
MAIL_EXISTING_ACCOUNT="mail_existing_account"
