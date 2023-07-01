echo "Mise en place du serveur"
cd ./Server
docker build -t f80hub/tokensol .
docker push f80hub/tokensol:latest

cd ..
putty -pw %1 -ssh root@192.168.1.62 -m "install_server_local.txt"

echo "Traitement terminé"
